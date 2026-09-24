#!/usr/bin/env python3
"""Load the Atenea Hackett+XDA logical export into the live Graphiti Neo4j.

Merges by uuid so a re-run is idempotent. Does not wipe existing nodes.

  NEO4J_PASSWORD=... python3 scripts/import-hackett-backup.py
  NEO4J_URI=bolt://192.168.15.2:7687 NEO4J_PASSWORD=... python3 scripts/import-hackett-backup.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKUP = ROOT / "backups" / "hackett-xda-current"
BATCH = 80


def parse_dt(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        return value
    text = value.replace("[UTC]", "")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def clean_props(props: dict) -> dict:
    out = {}
    for key, val in props.items():
        if val is None:
            continue
        if key in {"created_at", "valid_at", "invalid_at", "expired_at"}:
            parsed = parse_dt(val)
            if parsed is not None:
                out[key] = parsed
            continue
        out[key] = val
    return out


def chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def load_backup(path: Path):
    nodes = json.loads((path / "nodes.json").read_text())
    rels = json.loads((path / "relationships.json").read_text())
    eid_to_uuid = {n["element_id"]: n["properties"]["uuid"] for n in nodes}
    return nodes, rels, eid_to_uuid


def import_nodes(session, nodes) -> int:
    by_labels = defaultdict(list)
    for node in nodes:
        labels = tuple(node["labels"])
        props = clean_props(node["properties"])
        by_labels[labels].append({"uuid": props["uuid"], "props": props})

    total = 0
    for labels, rows in by_labels.items():
        label_cypher = ":".join(f"`{label}`" for label in labels)
        query = f"""
        UNWIND $rows AS row
        MERGE (n:{label_cypher} {{uuid: row.uuid}})
        SET n += row.props
        """
        for batch in chunks(rows, BATCH):
            session.run(query, rows=batch)
            total += len(batch)
        print(f"  nodes {':'.join(labels)} x{len(rows)}")
    return total


def import_rels(session, rels, eid_to_uuid) -> int:
    by_type = defaultdict(list)
    skipped = 0
    for rel in rels:
        start = eid_to_uuid.get(rel["start_element_id"])
        end = eid_to_uuid.get(rel["end_element_id"])
        props = clean_props(rel.get("properties") or {})
        uuid = props.get("uuid")
        if not start or not end or not uuid:
            skipped += 1
            continue
        # RELATES_TO already carries these; keep MENTIONS resolvable too
        props.setdefault("source_node_uuid", start)
        props.setdefault("target_node_uuid", end)
        by_type[rel["type"]].append(
            {"sid": start, "tid": end, "uuid": uuid, "props": props}
        )

    total = 0
    for rel_type, rows in by_type.items():
        query = f"""
        UNWIND $rows AS row
        MATCH (s {{uuid: row.sid}})
        MATCH (t {{uuid: row.tid}})
        MERGE (s)-[r:`{rel_type}` {{uuid: row.uuid}}]->(t)
        SET r += row.props
        """
        for batch in chunks(rows, BATCH):
            session.run(query, rows=batch)
            total += len(batch)
        print(f"  rels {rel_type} x{len(rows)}")
    if skipped:
        print(f"  skipped rels: {skipped}")
    return total


def ensure_vector_indexes(session) -> None:
    session.run(
        """
        CREATE VECTOR INDEX entity_name_embedding IF NOT EXISTS
        FOR (n:Entity) ON (n.name_embedding)
        OPTIONS {indexConfig: {
          `vector.dimensions`: 768,
          `vector.similarity_function`: 'cosine'
        }}
        """
    )
    session.run(
        """
        CREATE VECTOR INDEX fact_embedding IF NOT EXISTS
        FOR ()-[r:RELATES_TO]-() ON (r.fact_embedding)
        OPTIONS {indexConfig: {
          `vector.dimensions`: 768,
          `vector.similarity_function`: 'cosine'
        }}
        """
    )


def summarize(session) -> None:
    print("\n== live graph ==")
    print("nodes", session.run("MATCH (n) RETURN count(n) AS c").single()["c"])
    print("rels", session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"])
    print("by group:")
    for rec in session.run(
        """
        MATCH (n)
        WHERE n.group_id IS NOT NULL
        RETURN n.group_id AS g, count(*) AS c
        ORDER BY c DESC
        """
    ):
        print(f"  {rec['g']}: {rec['c']}")
    print("sample orgs:")
    for rec in session.run(
        """
        MATCH (n:Organization)
        RETURN n.group_id AS g, n.name AS name
        ORDER BY name
        LIMIT 20
        """
    ):
        print(f"  [{rec['g']}] {rec['name']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backup", type=Path, default=DEFAULT_BACKUP)
    ap.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://192.168.15.2:7687"))
    ap.add_argument("--user", default=os.environ.get("NEO4J_USER", "neo4j"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        print("Set NEO4J_PASSWORD", file=sys.stderr)
        return 2

    backup = args.backup.resolve()
    nodes, rels, eid_to_uuid = load_backup(backup)
    print(f"backup {backup.name}: {len(nodes)} nodes, {len(rels)} rels")
    if args.dry_run:
        return 0

    driver = GraphDatabase.driver(args.uri, auth=(args.user, password))
    try:
        with driver.session() as session:
            print("importing nodes")
            n = import_nodes(session, nodes)
            print("importing relationships")
            r = import_rels(session, rels, eid_to_uuid)
            print("vector indexes")
            ensure_vector_indexes(session)
            summarize(session)
            print(f"\nimported nodes={n} rels={r}")
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
