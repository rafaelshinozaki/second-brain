#!/usr/bin/env python3
"""Search the Atenea Hackett+XDA logical backup (not the live Windows graph).

Default path: backups/hackett-xda-current (symlink to the dated export).

  python3 scripts/search-hackett-backup.py "kimball assess"
  python3 scripts/search-hackett-backup.py --episodes-only "D-074"
  python3 scripts/search-hackett-backup.py --group hackett mirador-api
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "backups" / "hackett-xda-current"


def load_backup(path: Path) -> tuple[list[dict], list[dict]]:
    episodes = json.loads((path / "episodes.json").read_text())
    raw_nodes = json.loads((path / "nodes.json").read_text())
    entities = []
    for n in raw_nodes:
        labels = n.get("labels") or []
        if "Episodic" in labels:
            continue
        props = n.get("properties") or {}
        entities.append(
            {
                "name": props.get("name") or "",
                "group_id": props.get("group_id") or "",
                "labels": labels,
                "summary": props.get("summary") or "",
            }
        )
    return episodes, entities


def score(text: str, terms: list[str]) -> int:
    blob = text.lower()
    hits = sum(blob.count(t) for t in terms)
    if hits == 0:
        return 0
    if all(t in blob for t in terms):
        hits += 5
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="+")
    ap.add_argument("--backup", type=Path, default=DEFAULT)
    ap.add_argument("--group", action="append", default=[])
    ap.add_argument("--episodes-only", action="store_true")
    ap.add_argument("--max", type=int, default=12)
    args = ap.parse_args()

    backup = args.backup.resolve()
    if not (backup / "episodes.json").is_file():
        print(f"backup not found: {backup}", file=sys.stderr)
        return 2

    terms = [t.lower() for t in args.query]
    groups = set(args.group)
    episodes, entities = load_backup(backup)
    print(f"# {backup.name}  episodes={len(episodes)} entities={len(entities)}")
    print(f"# query: {' '.join(args.query)}")

    ranked: list[tuple[int, str]] = []
    for e in episodes:
        if groups and e.get("group_id") not in groups:
            continue
        text = f"{e.get('name','')}\n{e.get('content','')}"
        s = score(text, terms)
        if s:
            ranked.append((s, f"EPISODE [{e.get('group_id')}] {e.get('name')}\n{e.get('content','')}"))

    if not args.episodes_only:
        for n in entities:
            if groups and n["group_id"] not in groups:
                continue
            text = f"{n['name']}\n{n['summary']}"
            s = score(text, terms)
            if s:
                labels = ",".join(n["labels"])
                ranked.append((s, f"ENTITY [{n['group_id']}] ({labels}) {n['name']}\n{n['summary']}"))

    ranked.sort(key=lambda x: -x[0])
    if not ranked:
        print("no hits")
        return 1
    for i, (s, body) in enumerate(ranked[: args.max], 1):
        print(f"\n--- {i}  score={s} ---")
        print(body[:1200])
    if len(ranked) > args.max:
        print(f"\n... {len(ranked) - args.max} more hits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
