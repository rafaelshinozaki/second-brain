#!/usr/bin/env python3
"""Reconcile Abel's Atenea repo entities with Rafael's Mac clones.

Updates existing nodes (web_ui, app-api, mirador-api, studio, DIAL, Kimball)
and creates missing Repository nodes + SAME_AS / BELONGS_TO / CONSUMES edges
plus one Episodic memory in group `global`.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

from neo4j import GraphDatabase

NOW = datetime.now(timezone.utc)
GROUP = "global"
HACKETT_ORG = "2c39f810-740c-420d-befa-9fe82f018493"

# Existing Abel / earlier nodes
WEB_UI = "4919a510-8ad0-4979-aee5-ff48084328e2"
APP_API = "99d1f8ae-e0eb-4ff4-90ae-30437c378164"
MIRADOR = "218ced30-e001-4c12-9c47-a358009fe611"
STUDIO = "c0a5041c-ccde-46b3-bf17-0cb6cc559a25"
KAINAM_FRONT = "537f9593-4e11-46c7-859a-f6ff8cf304b4"
KIMBALL_TECH = "5c7f22cd-d791-4438-8476-84018a817523"
DIAL = "a388f61e-afff-4725-8b9e-6b2fa2a44937"
KAINAM_ORG = "ae4d50b1-e44d-4938-84ba-920fa8de7a74"

# New canonical nodes for Rafael's folder names
WEB_UI_AIX = "8a1c0e20-9f31-4b6a-a111-000000000001"
APP_API_AIX = "8a1c0e20-9f31-4b6a-a111-000000000002"
KAINAM_BE = "8a1c0e20-9f31-4b6a-a111-000000000003"
KIMBALL_ERP = "8a1c0e20-9f31-4b6a-a111-000000000004"
XDA_AZURE = "8a1c0e20-9f31-4b6a-a111-000000000005"
XDA_V2 = "8a1c0e20-9f31-4b6a-a111-000000000006"
EPISODE = "8a1c0e20-9f31-4b6a-a111-000000000100"


def uid(suffix: str) -> str:
    return str(uuid.uuid5(uuid.UUID("8a1c0e20-9f31-4b6a-a111-000000000000"), suffix))


UPDATES = [
    (
        WEB_UI,
        "web_ui repository",
        "AIX / AIXelerator Next.js frontend. Abel's clone was ~/Desktop/thehackettgroup/web_ui. "
        "Rafael's clone is /Users/rafaelsinosaki/Workspace/web-ui-aixelerator, same Azure DevOps repo "
        "thehackettgroup/AIEXELERATOR V2 - CPMXPLR/web-ui, branch dev. "
        "XDA consulting UI lives in components/aix-v3/xda and app/(v3)/xda. "
        "Stack: Next.js 16, React 19, Clerk, TypeScript, Vitest, Tailwind, AI Innovation design system. "
        "Final XDA product ships here, not in DIAL or jallen40/XDA. "
        "Talks to app-api and os-aixelerator-studio.",
    ),
    (
        APP_API,
        "app-api repository",
        "AIX / AIXelerator NestJS App API. Abel's clone was under the Azure AIEXELERATOR folder. "
        "Rafael's clone is /Users/rafaelsinosaki/Workspace/app-api-aixelerator, Azure DevOps "
        "thehackettgroup/AIEXELERATOR V2 - CPMXPLR/app-api, branch dev. "
        "XDA backend module is src/xda (roles in xda_roles, xda_canonical_contracts C1-C30). "
        "Stack: NestJS 11, MongoDB/Mongoose, Clerk JWT and API keys, Jest. "
        "Bridge 1 for Kimball is /api/xda/companies/:companyId/kimball/*.",
    ),
    (
        MIRADOR,
        "mirador-api",
        "Mirador AI conversation engine (NestJS, MongoDB, Clerk, Anthropic/OpenAI). "
        "Abel's Utz ops clone was ~/Desktop/thehackettgroup/mirador-api. "
        "Rafael's clone is /Users/rafaelsinosaki/Workspace/mirador-api, "
        "https://github.com/kainamAI/mirador-api.git branch mirador-api-v2. "
        "Utz production API: https://mirador.utz.kainam.app/api with X-User-Email. "
        "Consumed by kainam-front Mirador 3 and by Hackett Backoffice.",
    ),
    (
        STUDIO,
        "os-aixelerator-studio",
        "AIXelerator studio / OneStream Xelerator: FastAPI + LangGraph agents on Postgres. "
        "Abel cloned it 26 Aug 2026 to ~/Desktop/thehackettgroup/os-aixelerator-studio "
        "for the XDA Onboarding Assistant (INLINE_AGENTS, xda_onboarding toolbox). "
        "Rafael's clone is /Users/rafaelsinosaki/Workspace/os-aixelerator-studio, Azure DevOps "
        "thehackettgroup/AIEXELERATOR V2 - CPMXPLR/os-aixelerator-studio, "
        "branch feat/xda-engagement-rule-shapes.",
    ),
    (
        KAINAM_FRONT,
        "kainam-front",
        "Kainam platform frontend. Not in Abel's Atenea dump as this folder name. "
        "Rafael's clone is /Users/rafaelsinosaki/Workspace/kainam-front, "
        "https://github.com/kainamAI/kainam-front.git branch dev. "
        "Next.js 16 static export hosting Kimball, Senna, Monza, Mirador 3 and KAI with Keycloak OIDC. "
        "Consumes kainam-backend and mirador-api. Belongs to The Hackett Group (kainamAI org).",
    ),
    (
        KIMBALL_TECH,
        "Kimball Assess",
        "Kimball Assess is the Python FastAPI assessment engine used by XDA, distinct from Kainam ClickHouse "
        "and from Kimball v2 (/v2/* :8081). ERP fork lives in kainamAI/kimball-assess-erp "
        "(Rafael: /Users/rafaelsinosaki/Workspace/kimball-assess-erp). "
        "API prefix /api/v1/*, port 8300 direct or 3300 via gateway. "
        "Live ALB: kimball-assess-erp-dev-alb-374208137.us-east-2.elb.amazonaws.com. "
        "Hamad PR #10 (ingest:land) merged 8 Sep 2026 but was not on the ALB that day. "
        "D-074 said XDA should not depend on it as the engine; later work still audited the ERP fork.",
    ),
    (
        DIAL,
        "DIAL repository",
        "Abel's DIAL clone was ~/Desktop/thehackettgroup/DIAL: pnpm Turborepo with frontoffice, "
        "backoffice and an xda-api scaffold. One of two 50/50 reference sources for XDA UI "
        "(the other is jallen40/XDA). XDA does not ship from DIAL. "
        "Rafael's local folder /Users/rafaelsinosaki/Workspace/XDA is the Azure DevOps "
        "thehackettgroup/XDA repo (Hackett Backoffice, npm name hackett-backoffice), "
        "a related but separately cloned Backoffice/XEQ frontend — not the same path as Abel's DIAL.",
    ),
]

NEW_REPOS = [
    {
        "uuid": WEB_UI_AIX,
        "name": "web-ui-aixelerator",
        "summary": "Rafael's local folder name for the AIX web_ui repository. "
        "Path /Users/rafaelsinosaki/Workspace/web-ui-aixelerator. "
        "Same git remote as Abel's web_ui: Azure DevOps AIEXELERATOR V2 - CPMXPLR/web-ui, branch dev.",
    },
    {
        "uuid": APP_API_AIX,
        "name": "app-api-aixelerator",
        "summary": "Rafael's local folder name for the AIX app-api repository. "
        "Path /Users/rafaelsinosaki/Workspace/app-api-aixelerator. "
        "Same git remote as Abel's app-api: Azure DevOps AIEXELERATOR V2 - CPMXPLR/app-api, branch dev.",
    },
    {
        "uuid": KAINAM_BE,
        "name": "kainam-backend",
        "summary": "Kainam Python microservices monorepo (kai, kimball, senna, notifications, platform_config). "
        "Not present in Abel's Atenea dump. "
        "Rafael's clone: /Users/rafaelsinosaki/Workspace/kainam-backend, "
        "https://github.com/kainamAI/kainam-backend.git branch dev. "
        "PyNest/FastAPI, MongoDB, ClickHouse. Consumed by kainam-front. "
        "Distinct from Kimball Assess and from Kainam-the-ClickHouse-warehouse.",
    },
    {
        "uuid": KIMBALL_ERP,
        "name": "kimball-assess-erp",
        "summary": "ERP-only Kimball Assess fork. GitHub kainamAI/kimball-assess-erp. "
        "Rafael's clone: /Users/rafaelsinosaki/Workspace/kimball-assess-erp branch main. "
        "Python FastAPI, ClickHouse + MongoDB, port 8300, no frontend. "
        "Abel audited Hamad PR #10 (POST /runs/{id}/ingest:land) on 8 Sep 2026. "
        "Dev ALB kimball-assess-erp-dev-alb-374208137.us-east-2.elb.amazonaws.com.",
    },
    {
        "uuid": XDA_AZURE,
        "name": "XDA Azure / Hackett Backoffice",
        "summary": "Rafael's local folder /Users/rafaelsinosaki/Workspace/XDA is Hackett Backoffice "
        "(package.json name hackett-backoffice), Azure DevOps thehackettgroup/XDA branch develop. "
        "Turborepo with Next.js apps web (backoffice) and frontoffice (XEQ), Clerk, talks to mirador-api. "
        "Related to Abel's DIAL (original XDA/backoffice/frontoffice monorepo) but a different clone and remote. "
        "Not the XDA assessment prototype.",
    },
    {
        "uuid": XDA_V2,
        "name": "XDA_V2",
        "summary": "Jeff Allen's XDA pre-migration assessment prototype. "
        "GitHub jallen40/XDA, default branch main, live https://xda-ruby.vercel.app. "
        "Vanilla JS, no build, global XDA namespace. "
        "Rafael's clone: /Users/rafaelsinosaki/Workspace/XDA_V2. "
        "One of two 50/50 reference sources for XDA UI in web_ui (with DIAL). "
        "XDA does not ship from this repo.",
    },
]

EDGES = [
    (WEB_UI_AIX, WEB_UI, "SAME_AS", "web-ui-aixelerator is Rafael's local folder for Abel's web_ui repository."),
    (APP_API_AIX, APP_API, "SAME_AS", "app-api-aixelerator is Rafael's local folder for Abel's app-api repository."),
    (XDA_V2, WEB_UI, "REFERENCED_BY", "jallen40/XDA is a 50/50 reference source for XDA UI that ships in web_ui."),
    (DIAL, WEB_UI, "REFERENCED_BY", "DIAL is a 50/50 reference source for XDA UI that ships in web_ui."),
    (XDA_AZURE, DIAL, "RELATED_TO", "Rafael's Azure XDA/Hackett Backoffice clone is related to Abel's DIAL backoffice/frontoffice monorepo."),
    (XDA_AZURE, MIRADOR, "CONSUMES", "Hackett Backoffice consumes mirador-api."),
    (KAINAM_FRONT, MIRADOR, "CONSUMES", "kainam-front consumes mirador-api for Mirador 3."),
    (KAINAM_FRONT, KAINAM_BE, "CONSUMES", "kainam-front consumes kainam-backend for Kimball Senna Monza KAI."),
    (WEB_UI, APP_API, "CONSUMES", "web_ui talks to app-api for opportunity and XDA persistence."),
    (WEB_UI, STUDIO, "CONSUMES", "web_ui talks to os-aixelerator-studio for LangGraph / Axel agents."),
    (KIMBALL_ERP, KIMBALL_TECH, "IMPLEMENTS", "kimball-assess-erp is the ERP fork of Kimball Assess."),
    (APP_API, KIMBALL_ERP, "PROXIES_TO", "app-api Kimball bridge can proxy to Kimball Assess / kainam.apiUrl."),
]

for node_uuid, _name, _summary in UPDATES:
    EDGES.append((node_uuid, HACKETT_ORG, "BELONGS_TO", f"{_name} belongs to The Hackett Group."))
for repo in NEW_REPOS:
    EDGES.append((repo["uuid"], HACKETT_ORG, "BELONGS_TO", f"{repo['name']} belongs to The Hackett Group."))
EDGES.append((KAINAM_FRONT, KAINAM_ORG, "PART_OF", "kainam-front is the frontend of the Kainam product."))
EDGES.append((KAINAM_BE, KAINAM_ORG, "PART_OF", "kainam-backend is the Python services of the Kainam product."))
EDGES.append((MIRADOR, KAINAM_ORG, "SUPPORTS", "mirador-api supports the Mirador product on the Kainam platform."))

EPISODE_BODY = """Rafael Shinozaki Mac workspace reconciled with Abel Gonzalez's Atenea Second Brain export on 2026-09-16.

Name mapping (Abel / Azure / GitHub -> Rafael folder under /Users/rafaelsinosaki/Workspace):
- web_ui (Azure AIEXELERATOR web-ui) -> web-ui-aixelerator. Final XDA consulting UI ships here (components/aix-v3/xda).
- app-api (Azure AIEXELERATOR app-api) -> app-api-aixelerator. XDA backend is src/xda.
- os-aixelerator-studio (Azure AIEXELERATOR) -> os-aixelerator-studio. FastAPI LangGraph AI OS; XDA Onboarding Assistant.
- mirador-api (Abel's ~/Desktop/thehackettgroup/mirador-api, Utz ops) -> mirador-api on github.com/kainamAI/mirador-api branch mirador-api-v2.
- jallen40/XDA (Jeff Vercel prototype xda-ruby.vercel.app) -> XDA_V2. Reference only; XDA does not ship from here.
- DIAL (Abel's original XDA/backoffice/frontoffice monorepo) is a reference source. Rafael's folder XDA is Azure thehackettgroup/XDA Hackett Backoffice (hackett-backoffice), related but a different clone.
- kainamAI/kimball-assess-erp (Hamad PR #10 ingest:land, ALB in us-east-2) -> kimball-assess-erp. ERP-only Kimball Assess fork, port 8300. Distinct from Kainam ClickHouse and Kimball v2 :8081.
- kainam-front and kainam-backend were not in Abel's dump. They are kainamAI GitHub repos on Rafael's Mac: Next.js Kainam shell and the Python kai/kimball/senna monorepo.

All of these product repos belong to The Hackett Group. kainamAI GitHub and Azure DevOps thehackettgroup are Hackett orgs.
Do not implement XDA features in DIAL or in jallen40/XDA. Do not treat Kainam, Kimball v2 and Kimball Assess as the same backend.
"""


def merge_entity(tx, node_uuid: str, name: str, summary: str, extra_labels: list[str]) -> None:
    label_set = "".join(f"SET n:`{label}` " for label in extra_labels)
    tx.run(
        f"""
        MERGE (n:Entity {{uuid: $uuid}})
        ON CREATE SET n.created_at = $now, n.group_id = $group
        SET n.name = $name,
            n.summary = $summary,
            n.group_id = coalesce(n.group_id, $group),
            n.labels = $lab_prop
        {label_set}
        """,
        uuid=node_uuid,
        name=name,
        summary=summary,
        now=NOW,
        group=GROUP,
        lab_prop=["Entity", *extra_labels],
    )


def merge_edge(tx, source: str, target: str, name: str, fact: str) -> None:
    edge_uuid = uid(f"{source}|{name}|{target}")
    tx.run(
        """
        MATCH (s {uuid: $sid})
        MATCH (t {uuid: $tid})
        MERGE (s)-[r:RELATES_TO {uuid: $eu}]->(t)
        SET r.name = $name,
            r.fact = $fact,
            r.group_id = $group,
            r.created_at = coalesce(r.created_at, $now),
            r.source_node_uuid = $sid,
            r.target_node_uuid = $tid,
            r.episodes = [$ep]
        """,
        sid=source,
        tid=target,
        eu=edge_uuid,
        name=name,
        fact=fact,
        group=GROUP,
        now=NOW,
        ep=EPISODE,
    )


def main() -> int:
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        print("Set NEO4J_PASSWORD", file=sys.stderr)
        return 2
    uri = os.environ.get("NEO4J_URI", "bolt://192.168.15.2:7687")
    driver = GraphDatabase.driver(uri, auth=("neo4j", password))
    mentioned = [WEB_UI, APP_API, MIRADOR, STUDIO, KAINAM_FRONT, KIMBALL_TECH, DIAL, HACKETT_ORG]
    mentioned += [r["uuid"] for r in NEW_REPOS]
    try:
        with driver.session() as session:
            with session.begin_transaction() as tx:
                for node_uuid, name, summary in UPDATES:
                    extra = ["Repository"] if node_uuid != KIMBALL_TECH else ["Technology"]
                    if node_uuid == STUDIO:
                        extra = ["Repository", "Server"]
                    merge_entity(tx, node_uuid, name, summary, extra)
                    print("updated", name)

                for repo in NEW_REPOS:
                    merge_entity(tx, repo["uuid"], repo["name"], repo["summary"], ["Repository"])
                    print("created", repo["name"])

                tx.run(
                    """
                    MERGE (e:Episodic {uuid: $uuid})
                    SET e.name = $name,
                        e.content = $content,
                        e.group_id = $group,
                        e.source = 'text',
                        e.source_description = 'Rafael Mac workspace x Abel Atenea backup 2026-09-16',
                        e.created_at = $now,
                        e.valid_at = $now,
                        e.entity_edges = $edges
                    """,
                    uuid=EPISODE,
                    name="Rafael Mac repos reconciled with Abel Atenea backup",
                    content=EPISODE_BODY,
                    group=GROUP,
                    now=NOW,
                    edges=mentioned,
                )
                print("episode written")

                for source, target, name, fact in EDGES:
                    merge_edge(tx, source, target, name, fact)
                print("edges", len(EDGES))

                for target in mentioned:
                    mention_uuid = uid(f"mention|{EPISODE}|{target}")
                    tx.run(
                        """
                        MATCH (e:Episodic {uuid: $ep})
                        MATCH (n {uuid: $tid})
                        MERGE (e)-[r:MENTIONS {uuid: $mu}]->(n)
                        SET r.group_id = $group, r.created_at = $now
                        """,
                        ep=EPISODE,
                        tid=target,
                        mu=mention_uuid,
                        group=GROUP,
                        now=NOW,
                    )
                tx.commit()

            rec = session.run(
                """
                MATCH (e:Episodic {uuid: $ep})
                OPTIONAL MATCH (e)-[:MENTIONS]->(n)
                RETURN e.name AS name, count(n) AS mentions
                """,
                ep=EPISODE,
            ).single()
            print("verify episode", rec["name"], "mentions", rec["mentions"])
            for rec in session.run(
                """
                MATCH (r:Repository)
                WHERE r.uuid IN $ids OR r.name IN $names
                RETURN r.name AS name, r.group_id AS g
                ORDER BY name
                """,
                ids=[r["uuid"] for r in NEW_REPOS] + [WEB_UI, APP_API, MIRADOR, STUDIO, KAINAM_FRONT, XDA_AZURE],
                names=["web-ui-aixelerator", "kainam-backend", "kimball-assess-erp", "XDA_V2"],
            ):
                print(f"  repo [{rec['g']}] {rec['name']}")
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
