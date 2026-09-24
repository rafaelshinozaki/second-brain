#!/usr/bin/env python3
"""Enrich Second Brain with corrections from the 2026-09-16 deep repo scans.

Key names only. No secret values.
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
WEB_UI = "4919a510-8ad0-4979-aee5-ff48084328e2"
APP_API = "99d1f8ae-e0eb-4ff4-90ae-30437c378164"
MIRADOR = "218ced30-e001-4c12-9c47-a358009fe611"
STUDIO = "c0a5041c-ccde-46b3-bf17-0cb6cc559a25"
KAINAM_FRONT = "537f9593-4e11-46c7-859a-f6ff8cf304b4"
KAINAM_BE = "8a1c0e20-9f31-4b6a-a111-000000000003"
KIMBALL_ERP = "8a1c0e20-9f31-4b6a-a111-000000000004"
XDA_AZURE = "8a1c0e20-9f31-4b6a-a111-000000000005"
XDA_V2 = "8a1c0e20-9f31-4b6a-a111-000000000006"
KAINAM_FORGE = "8a1c0e20-9f31-4b6a-a111-000000000008"
MONZA_SVC = "8a1c0e20-9f31-4b6a-a111-000000000009"
EP = "8a1c0e20-9f31-4b6a-a111-000000000220"


def uid(suffix: str) -> str:
    return str(uuid.uuid5(uuid.UUID("8a1c0e20-9f31-4b6a-a111-000000000000"), suffix))


CONTENT = """Corrections and enrichments after deep scans of the Hackett Mac workspace on 2026-09-16. These override earlier operational-map claims where they conflict.

kainam-front: Nx 23 + pnpm workspace, products are packages with ESLint module-boundary gates. public/config.json replaces defaults wholesale — no key-by-key merge; add new keys to both public/config.json and libs/platform/config/src/config.default.json. Never call getConfig() at module scope; await loadConfig() first. Missing config key shows coming soon, does not crash. planning, adm, AFR, account-reconciliation are iframe placeholders via @kainam/embed, not native UIs. MIRADOR3_API_URL talks to kainam-forge (control plane, not in this workspace). MONZA_API_URL is a separate OLAP deploy, not kainam-backend. Deploy: static out/ to S3+CloudFront and Azure Blob. Build-time env names: NEXT_PUBLIC_AUTH_BYPASS, NEXT_PUBLIC_APP_VERSION, NEXT_PUBLIC_APP_RELEASE_DATE, NEXT_PUBLIC_DOCUMENTATION_URL, NEXT_PUBLIC_SUPER_ADMIN_ROLES, NEXT_PUBLIC_KEYCLOAK_URL, NEXT_PUBLIC_KEYCLOAK_ADMIN_URL, NEXT_PUBLIC_MONZA_*, NEXT_PUBLIC_BASE_PATH, KAINAM_DEV_NO_EXPORT, KAINAM_DIST_DIR, PORT. Local Keycloak redirect is registered for localhost:3000 only. Use pnpm serve:cloudfront to test static out/, not serve:spa.

kainam-backend: Shared local infra is src/kimball/docker-compose (ClickHouse, Mongo, Redis, MinIO). Root docker-compose.yml is notifications only. Kai and Kimball both historically default toward 8000/8081 — always pass explicit --port. Senna port 8080 is hardcoded; manage.py is at src/senna root. PyNest 0.6.2 on kai/kimball vs 0.4.0 on senna/platform_config/notifications. Kimball extra contexts: artifacts, ssi_library, worker. Senna extra: eda, kmodel, bizdev, external_factors. EXECUTION_MODE=api for local Kimball without a Celery worker. Mongo DB names must differ per service. CI: CircleCI to AWS ECR + Azure ACR. Notifications production expects gateway-injected X-Access-Token and X-Forwarded-Email.

mirador-api: Runtime user auth is GatewayAuthGuard — requires X-User-Email (plus optional X-User-Id / X-User-Name) from the platform gateway. README Clerk mentions are historical. Admin/config routes (flows, prompts, variables, ai-config, access, health) have no controller guard — backoffice/internal. Production: AWS ECS Fargate + ALB + ECR + SSM. KIMBALL_API_URL here is kainam-backend v2, never kimball-assess-erp.

kimball-assess-erp: Permanent ERP-only fork (branch_scope.enabled_domains erp, live profile erp_transition). No UI in the repo; :3300 is a leftover CORS placeholder. Primary HTTP consumer is XDA frontoffice / web-ui assess proxy with XDA_ASSESS_API_URL, XDA_ASSESS_API_KEY, XDA_ASSESS_CLIENT (key names). kainam-front config.json does not point at Assess. AWS dev: ALB to EC2 m6i.large us-east-2, ClickHouse+Mongo on localhost systemd, S3 files, SSM not SSH. OpenAPI ~147 paths under /api/v1. Heavy ops return 202 + Location job. Studio xda_assess_* tools embed rules locally and do not have to HTTP this API.

web-ui-aixelerator: There is no src/xda folder. XDA UI is components/aix-v3/xda plus app/(v3)/xda and opportunity-scoped .../xda/*. frontoffice/ under that package is the old XDA/apps/frontoffice shell, not XDA_V2.

app-api-aixelerator: Also has src/api/v3 (projects, opportunity-overview, chat SSE proxy to studio, process-flows, solutions, mcp, xt, xda-rule-library). Mongo owns opportunity documents. Studio Postgres owns workflow/vector/queue. Data split: web-ui never talks to a database.

os-aixelerator-studio XDA agents (SSE /api/ai-execution/chat/stream/{slug}): xda-onboarding-assistant, xda-intake-assistant, xda-assess-assistant, xda-curation-author, xda-baseline-assistant. Typical chain: web-ui assistant.ts → app-api POST /api/v3/chat/stream/{slug} → studio → tools call app-api with AIX_XDA_API_KEY.

XDA folder (hackett-backoffice): NestJS that used to live here migrated to mirador-api. apps/xda-api is Phase 0 health-only stub on :3010, not a full tenancy API yet. Package name hackett-backoffice. pnpm 11 + Turborepo. Frontoffice README says XEQ Front Office; UI metadata says XDA.

XDA_V2: serve.ps1 on localhost:8619. No mirador-api, no app-api, no Kimball in the live assessment path. Methodology reference only.
"""


def main() -> int:
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        print("Set NEO4J_PASSWORD", file=sys.stderr)
        return 2
    uri = os.environ.get("NEO4J_URI", "bolt://192.168.15.2:7687")
    driver = GraphDatabase.driver(uri, auth=("neo4j", password))
    mentioned = [
        HACKETT_ORG,
        KAINAM_FRONT,
        KAINAM_BE,
        MIRADOR,
        KIMBALL_ERP,
        WEB_UI,
        APP_API,
        STUDIO,
        XDA_AZURE,
        XDA_V2,
        KAINAM_FORGE,
        MONZA_SVC,
    ]
    try:
        with driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run(
                    """
                    MERGE (n:Entity {uuid: $uuid})
                    ON CREATE SET n.created_at = $now, n.group_id = $group
                    SET n.name = $name,
                        n.summary = $summary,
                        n.group_id = coalesce(n.group_id, $group),
                        n.labels = $labs
                    SET n:Repository
                    """,
                    uuid=KAINAM_FORGE,
                    name="kainam-forge",
                    summary=(
                        "kainam-forge is the Mirador 3 control plane. "
                        "kainam-front talks to it via MIRADOR3_API_URL. "
                        "Not cloned in Rafael's current Cursor workspace."
                    ),
                    now=NOW,
                    group=GROUP,
                    labs=["Entity", "Repository"],
                )
                tx.run(
                    """
                    MERGE (n:Entity {uuid: $uuid})
                    ON CREATE SET n.created_at = $now, n.group_id = $group
                    SET n.name = $name,
                        n.summary = $summary,
                        n.group_id = coalesce(n.group_id, $group),
                        n.labels = $labs
                    SET n:Service
                    """,
                    uuid=MONZA_SVC,
                    name="Monza OLAP service",
                    summary=(
                        "Monza is a separate OLAP / XMLA deploy. "
                        "kainam-front uses MONZA_API_URL. Kai talks to it via MONZA_MCP_URL. "
                        "It is not a service inside kainam-backend."
                    ),
                    now=NOW,
                    group=GROUP,
                    labs=["Entity", "Service"],
                )
                tx.run(
                    """
                    MATCH (n {uuid: $uuid})
                    SET n.summary = $summary
                    """,
                    uuid=MIRADOR,
                    summary=(
                        "mirador-api is the NestJS 11 AI conversation engine. "
                        "Docker host :3001 → app :3000. Mongo wallah. "
                        "User routes use GatewayAuthGuard (X-User-Email from the platform gateway); "
                        "README Clerk mentions are historical. "
                        "Admin routes (flows/prompts/ai-config) are unguarded. "
                        "KIMBALL_API_URL is kainam-backend v2, not kimball-assess-erp. "
                        "Prod: ECS Fargate + ALB. Consumed by kainam-front Mirador and Hackett Backoffice."
                    ),
                )
                tx.run(
                    """
                    MATCH (n {uuid: $uuid})
                    SET n.summary = $summary
                    """,
                    uuid=XDA_AZURE,
                    summary=(
                        "XDA folder is Azure thehackettgroup/XDA package hackett-backoffice "
                        "(not DIAL clone, not jallen40/XDA). "
                        "backoffice Next :3000/3003, frontoffice :4000, xda-api Nest :3010 health-only stub. "
                        "Former Nest API moved to mirador-api. Clerk + REQUIRED_ORG_SLUG=xeq. "
                        "Frontoffice README says XEQ; UI metadata says XDA."
                    ),
                )
                tx.run(
                    """
                    MATCH (n {uuid: $uuid})
                    SET n.summary = $summary
                    """,
                    uuid=KAINAM_FRONT,
                    summary=(
                        "kainam-front is the Kainam Next.js 16 static-export shell (Nx + pnpm). "
                        "Runtime public/config.json replaces defaults wholesale; not a .env. "
                        "Local :3000, Keycloak, THEME=xeq dashboard else kiosk. "
                        "Native products: kimball, senna, monza, mirador, mirador-3, kai. "
                        "planning/adm/AFR/AR are remote iframes. "
                        "MIRADOR3_API_URL → kainam-forge. MONZA_API_URL is a separate OLAP service. "
                        "Does not call kimball-assess-erp."
                    ),
                )
                tx.run(
                    """
                    MERGE (e:Episodic {uuid: $uuid})
                    SET e.name = $name,
                        e.content = $content,
                        e.group_id = $group,
                        e.source = 'text',
                        e.source_description = 'Deep scan corrections 2026-09-16',
                        e.created_at = $now,
                        e.valid_at = $now,
                        e.entity_edges = $edges
                    """,
                    uuid=EP,
                    name="Hackett workspace scan corrections 2026-09-16",
                    content=CONTENT,
                    group=GROUP,
                    now=NOW,
                    edges=mentioned,
                )
                for target in mentioned:
                    tx.run(
                        """
                        MATCH (e:Episodic {uuid: $ep})
                        MATCH (n {uuid: $tid})
                        MERGE (e)-[r:MENTIONS {uuid: $mu}]->(n)
                        SET r.group_id = $group, r.created_at = $now
                        """,
                        ep=EP,
                        tid=target,
                        mu=uid(f"mention|{EP}|{target}"),
                        group=GROUP,
                        now=NOW,
                    )
                for source, target, name, fact in [
                    (
                        KAINAM_FRONT,
                        KAINAM_FORGE,
                        "CONSUMES",
                        "kainam-front Mirador 3 calls kainam-forge via MIRADOR3_API_URL.",
                    ),
                    (
                        KAINAM_FRONT,
                        MONZA_SVC,
                        "CONSUMES",
                        "kainam-front Monza UI calls the separate Monza OLAP service via MONZA_API_URL.",
                    ),
                    (
                        KAINAM_BE,
                        MONZA_SVC,
                        "CONSUMES",
                        "Kai talks to Monza over MCP using MONZA_MCP_URL. Monza is not inside kainam-backend.",
                    ),
                    (
                        XDA_AZURE,
                        KIMBALL_ERP,
                        "CONSUMES",
                        "XDA frontoffice / web-ui assess proxy is the primary HTTP client of kimball-assess-erp.",
                    ),
                ]:
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
                        eu=uid(f"{source}|{name}|{target}|corr"),
                        name=name,
                        fact=fact,
                        group=GROUP,
                        now=NOW,
                        ep=EP,
                    )
                tx.commit()
            rec = session.run(
                "MATCH (e:Episodic {uuid: $ep}) OPTIONAL MATCH (e)-[:MENTIONS]->(n) "
                "RETURN e.name AS name, count(n) AS m",
                ep=EP,
            ).single()
            print("episode", rec["name"], "mentions", rec["m"])
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
