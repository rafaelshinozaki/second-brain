#!/usr/bin/env python3
"""Write per-repo operational memories (purpose, modules, env KEY NAMES, infra).

Never store secret values. Key names only. Run:

  NEO4J_URI=bolt://192.168.15.2:7687 NEO4J_PASSWORD=... \\
    python3 scripts/upsert-repo-ops.py
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
KIMBALL_TECH = "5c7f22cd-d791-4438-8476-84018a817523"
WEB_UI_AIX = "8a1c0e20-9f31-4b6a-a111-000000000001"
APP_API_AIX = "8a1c0e20-9f31-4b6a-a111-000000000002"
KAINAM_BE = "8a1c0e20-9f31-4b6a-a111-000000000003"
KIMBALL_ERP = "8a1c0e20-9f31-4b6a-a111-000000000004"
XDA_AZURE = "8a1c0e20-9f31-4b6a-a111-000000000005"
XDA_V2 = "8a1c0e20-9f31-4b6a-a111-000000000006"
SECOND_BRAIN = "8a1c0e20-9f31-4b6a-a111-000000000007"
MASTER_EP = "8a1c0e20-9f31-4b6a-a111-000000000200"


def uid(suffix: str) -> str:
    return str(uuid.uuid5(uuid.UUID("8a1c0e20-9f31-4b6a-a111-000000000000"), suffix))


# Compact summaries written onto Repository nodes (searchable, not a dump).
SUMMARIES = {
    KAINAM_FRONT: (
        "kainam-front is the Kainam Next.js 16 static-export shell (output: export). "
        "Runtime config is public/config.json (copy from example.config.json or public.json), not a .env. "
        "Local UI :3000. Auth Keycloak. Theme THEME=xeq shows product dashboard; default theme is the kiosk Launchpad. "
        "Product libs: kimball, senna, monza, mirador, mirador-3, planning, adm, AFR, account-reconciliation. "
        "Talks to kainam-backend (kai :8000, kimball :8081, senna :8080, notifications :8085, platform_config :8003) and mirador-api :3001."
    ),
    KAINAM_BE: (
        "kainam-backend is a Python monorepo of FastAPI/PyNest services. "
        "kai :8000 chat+ontology+MCP orchestration; kimball :8081 data-pipeline DAG on ClickHouse + MCP; "
        "senna :8080 ML flows + Celery/Redis; notifications :8085; platform_config :8003. "
        "Shared infra: MongoDB :27017, ClickHouse :8123, Redis :6379, S3/MinIO. Auth Keycloak JWKS. "
        "Each service has its own src/<svc>/example.env. Owner kainamAI / The Hackett Group."
    ),
    MIRADOR: (
        "mirador-api is the NestJS 11 AI conversation engine. Docker Compose maps host :3001 → app :3000. "
        "Mongo wallah, Clerk JWT, SSE chat. Providers Anthropic, OpenAI, Azure Foundry, AWS Bedrock. "
        "Modules: chat, flows, prompts, variables, ai-config, kimball (easy-import/DDL), senna, mcp, storage, "
        "state-machine, access-query, data-viewer, templates. Consumed by kainam-front Mirador and Hackett Backoffice."
    ),
    KIMBALL_ERP: (
        "kimball-assess-erp is the ERP-only Kimball Assess FastAPI on :8300 (MCP optional :8310). "
        "ClickHouse schema assess + Mongo assess_meta. Local file store data/_assess. "
        "Auth ASSESS_API_KEY / ASSESS_AUTH_MODE=dev. Distinct from Kimball v2 :8081 and Kainam ClickHouse. "
        "Modules: api, assess, packs, mcp, sql, repositories, services. GitHub kainamAI/kimball-assess-erp."
    ),
    WEB_UI: (
        "web_ui / web-ui-aixelerator is the AIX Next.js 16 + React 19 frontend (Clerk, Tailwind, AI Innovation DS). "
        "XDA consulting UI is components/aix-v3/xda and app/(v3)/xda. Talks to app-api and studio. "
        "Config via NEXT_PUBLIC_* env (no rich .env.example). Assess proxy uses NEXT_PUBLIC_ASSESS_CLIENT/ACTOR/ROLES. "
        "Azure DevOps AIEXELERATOR V2 - CPMXPLR/web-ui, branch dev. Final XDA product ships here."
    ),
    APP_API: (
        "app-api / app-api-aixelerator is NestJS 11 + Mongo aixelerator + Clerk JWT and axk_live_ API keys. "
        "Port 3000. XDA lives in src/xda (companies, roles, canonical C1-C30, kimball bridge, chat, impersonation). "
        "~40 v1 modules: discovery, surveys, agents, RTM, vendor-eval, intelligence, chain-execution. "
        "Calls OS_API_URL (aix-ai-api) and OS_STUDIO_API_URL (studio). Tenant keys AIX_<SLUG>_API_KEY on studio side."
    ),
    STUDIO: (
        "os-aixelerator-studio is FastAPI + LangGraph on Postgres (DATABASE_URL), default uvicorn :8000. "
        "AWS profile aixelerator + S3_BUCKET_NAME required. Tenant auth AIX_<SLUG>_API_KEY (axk_live_). "
        "Modules include agent_harness, agent_toolkit, atlas, onestream_mcp, workplan_v6, document_vectorizer, "
        "sales_intelligence, phoenix observability. XDA Onboarding Assistant and Kimball Assess tools live here."
    ),
    XDA_AZURE: (
        "XDA folder on Rafael's Mac is Azure thehackettgroup/XDA Hackett Backoffice (not DIAL, not jallen40/XDA). "
        "Apps: backoffice Next :3000/3003, frontoffice Next :4000, xda-api Nest :3010 Mongo xda. "
        "Shared Clerk keys across backoffice, frontoffice, and mirador-api. REQUIRED_ORG_SLUG=xeq. "
        "Frontoffice XT Assistant uses AWS Bedrock. Local port map: mirador-api :3001, FO :4000, BO :3000."
    ),
    XDA_V2: (
        "XDA_V2 is jallen40/XDA: static vanilla JS + Supabase, no build step. Reference / Jeff prototype only. "
        "Config in js/config.js (public anon key; RLS is auth; never service_role). Anthropic only via assist Edge Function. "
        "XDA does not ship from here. Demo composites must stay 65, 65, 89, 78, 91.7, 48, 86.8."
    ),
    WEB_UI_AIX: (
        "Rafael Mac folder name for Abel's web_ui: /Users/rafaelsinosaki/Workspace/web-ui-aixelerator. SAME_AS web_ui."
    ),
    APP_API_AIX: (
        "Rafael Mac folder name for Abel's app-api: /Users/rafaelsinosaki/Workspace/app-api-aixelerator. SAME_AS app-api."
    ),
    SECOND_BRAIN: (
        "second-brain is Rafael's Graphiti MCP + Neo4j knowledge graph. Live instance on Windows LAN 192.168.15.2. "
        "MCP http://192.168.15.2:8020/mcp (Host 127.0.0.1:8020 or mac-mcp-host-proxy). Neo4j Browser :7474 bolt :7687. "
        "Embeddings Ollama nomic-embed-text 768-dim. Groups: global, software, hackett, plus Mac hackett-workspace/aixelerator/xda. "
        "add_memory is broken (QueueService.add_episode reference_time); writes go via Cypher MERGE by uuid."
    ),
}

EPISODES = [
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000201",
        "name": "kainam-front operational map 2026-09-16",
        "repo": KAINAM_FRONT,
        "mentions": [KAINAM_FRONT, KAINAM_BE, MIRADOR, HACKETT_ORG],
        "content": """kainam-front (github.com/kainamAI/kainam-front) is The Hackett Group Kainam product shell.

Purpose: single static-export Next.js 16 frontend for Kimball, Senna, Monza, Mirador, Mirador 3, Planning, ADM, AFR, Account Reconciliation, plus kiosk launchpad.

How it works: output export. Identifiers go in query strings, never path segments, except three leftover [param] routes. After login, THEME in public/config.json chooses home: xeq = product dashboard + Header; empty/default = full-screen kiosk Launchpad from ConditionalHeader. Two role models: productAccess (kimball-user/admin/view) and kiosk app.* / engine.* via mapKeycloakRolesToKiosk.

Config: NO dotenv for product URLs. Runtime public/config.json (gitignored). Seed from example.config.json or public/public.json. AppConfig in libs/platform/config/src/config.ts.

Runtime keys (names only): SENNA_API_URL, SENNA_URL, KIMBALL_API_URL, KAI_API_URL, KAI_CHAT_TRANSPORT, MIRADOR_API_URL, MIRADOR_URL, MIRADOR3_API_URL, USE_MIRADOR3_MOCKS, MIRADOR3_LAB_TOKEN, MONZA_API_URL, MONZA_DEFAULT_OLAP_URL, MONZA_DEFAULT_CONNECTION_NAME, MONZA_DEFAULT_CATALOG, MONZA_CONNECTION_MODE, MONZA_HOST, MONZA_PORT, ONTOLOGY_API_URL, ONTOLOGY_INGESTION_ENABLED, ONTOLOGY_LEARNING_ENABLED, PLATFORM_CONFIG_API_URL, NOTIFICATIONS_API_URL, CONSOLIDATION_API_URL, CONSOLIDATION_ENGINE_URL, AFR_API_URL, AFR_API_KEY, AFR_TENANT, AFR_ROLES, AFR_ACTOR, AUGMENTED_FINANCIAL_REPORTING_URL, ACCOUNT_RECONCILIATION_URL, PLANNING_URL, ADM_URL, MDM_API_URL, MDM_API_KEY, MDM_TENANT, MDM_ROLES, MDM_ACTOR, KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID, KEYCLOAK_ADMIN_URL, AUTH_BYPASS, THEME, PADDOCK_URL, AUGMENTED_TAX_MANAGEMENT_URL, EMBED_AUTH_HMAC_SECRET, DOWNLOADS_BASE_URL, DOWNLOADS_ENV, DEFAULT_SCHEMA, USE_DATASET_MOCKS, USE_CONSOLIDATION_MOCKS, API_BASE_PATH, API_TIMEOUT, APP_URL.

example.config.json is a subset and omits KAI_API_URL / KIMBALL_API_URL / SENNA_API_URL / THEME — those still exist on AppConfig.

Modules (libs/products): kimball (pipelines/ERD/lineage UI), senna (ML flow wizard), monza (OLAP cubes; calendar filter workaround in libs/integrations/ktable), mirador (generated-app chat), mirador-3 (control-plane workspace), planning, adm (MDM), augmented-financial-reporting, account-reconciliation. Platform: themes, http, config, embed, kiosk.

Infra: static files behind CDN/nginx; local :3000. Auth Keycloak. Talks to kainam-backend services and mirador-api. Never expose endpoints/table names in UI copy.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000202",
        "name": "kainam-backend operational map 2026-09-16",
        "repo": KAINAM_BE,
        "mentions": [KAINAM_BE, KAINAM_FRONT, KIMBALL_TECH, HACKETT_ORG],
        "content": """kainam-backend (github.com/kainamAI/kainam-backend) is The Hackett Group Python backend monorepo.

Purpose: five independently configured FastAPI/PyNest services sharing Mongo/ClickHouse/Redis/S3 patterns.

Services and ports:
- kai :8000 — KAI chat, ontology library ingest/learn, MCP client to Kimball/Monza/Senna/ontology. Modules under src/kai (chat, ontology, orchestration). Auth Keycloak. example.env keys: DEBUG, TIMEZONE, GENERAL_DB_URL, GENERAL_DB_NAME, CORS_*, KEYCLOAK_ISSUER_URL, KEYCLOAK_AUDIENCE, KEYCLOAK_JWKS_URL, ANTHROPIC_API_KEY, OPENAI_API_KEY, AWS_ACCESS_KEY_ID, AWS_PROFILE, AWS_REGION, MONZA_MCP_URL, MONZA_MCP_CONFIRMATION_SECRET, KIMBALL_MCP_URL, KIMBALL_MCP_CONFIRMATION_SECRET, SENNA_MCP_URL, SENNA_MCP_CONFIRMATION_SECRET, ONTOLOGY_MCP_URL, ONTOLOGY_LIBRARY_REST_URL, ONTOLOGY_SOURCE, ONTOLOGY_GROUP_IDS, ONTOLOGY_CONTEXT_MAX_CHARS, ONTOLOGY_CONTEXT_TTL_SECONDS, ONTOLOGY_MCP_TIMEOUT, ONTOLOGY_INGESTION_MCP_TIMEOUT, ONTOLOGY_INGESTION_ENABLED, ONTOLOGY_MAX_ARCHIVE_MB, PLATFORM_ORG_ID, ONTOLOGY_LEARNING_ENABLED, ONTOLOGY_SIGNAL_*, ONTOLOGY_SESSION_*, ONTOLOGY_LEARNING_DEFAULT_GROUP_ID, NOTIFICATIONS_API_URL, NOTIFICATIONS_SERVICE_TOKEN, ORCHESTRATION_MCP_ENDPOINTS, ORCHESTRATION_RUN_TTL_SECONDS.
- kimball :8081 + /mcp — hexagonal data-pipeline API. Bounded contexts: pipeline (SQL DAG + PipelineExecutor), source (connectors, file-upload presign), data_catalog, data_intelligence (ERD, lineage, column lineage), event_bus, managed (dim_period etc), assessment (discover/type_inference/duplicates/cleansing/erd/hierarchies + extended EPM), relay, parc_ferme. ClickHouse warehouse + Mongo metadata + S3 stage. example.env: GENERAL_DB_*, CLICKHOUSE_HOST/PORT/USERNAME/PASSWORD/DATABASE/SECURE, CONNECTOR_FERNET_KEY, BUCKET_NAME, AWS_*, AWS_S3_ENDPOINT_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CELERY_LOCAL, EXECUTION_MODE, KIMBALL_MCP_*, KEYCLOAK_*, PARC_FERME_*, NOTIFICATIONS_*, anthropic_api_key.
- senna :8080 — ML workflow API (DDD). Contexts: ml_flows (state machine Churn/TimeSeries), datasets, scenarios, shared. Celery workers, Redis broker, S3 kmodels, Mongo senna_dev, ClickHouse analytics. example.env: LOCAL, GENERAL_DB_*, REDIS_HOST/PORT/DB/PASSWORD, CELERY_BROKER_URL, CELERY_BACKEND_URL, S3_BUCKET_NAME, S3_DATASET_BASE_PATH, AWS_DEFAULT_REGION, DEBUG, ENVIRONMENT, LOG_LEVEL, NOTIFICATIONS_*, SENNA_MCP_*, KEYCLOAK_*.
- notifications :8085 — notifications center. Mongo notifications. Keys: NOTIFICATIONS_PORT, NOTIFICATIONS_MONGO_URL, NOTIFICATIONS_DB_NAME, NOTIFICATIONS_SERVICE_TOKEN, NOTIFICATIONS_ADMIN_SERVICE_TOKEN, NOTIFICATIONS_ALLOWED_SOURCE_APPS, NOTIFICATIONS_CALLBACK_*, NOTIFICATIONS_TENANT_CLAIM, NOTIFICATIONS_LEGACY_TENANT_ID, NOTIFICATIONS_REQUIRE_TENANT, NOTIFICATIONS_ADMIN_ROLE, NOTIFICATIONS_EMAIL_*, NOTIFICATIONS_PUBLIC_APP_URL, NOTIFICATIONS_RETENTION_DAYS, AWS_REGION, KEYCLOAK_*, CORS_*.
- platform_config :8003 — branding/theme/product flags for the shell. Keys: API_PORT, GENERAL_DB_URL, GENERAL_DB_NAME=platform_config, KEYCLOAK_*, CORS_*, PLATFORM_CONFIG_ADMIN_ROLES.

Infra: Mongo :27017, ClickHouse :8123, Redis :6379, MinIO often :9100 (Kimball). Root docker-compose.yml currently wires notifications + Mongo on network kainam-platform. Kimball has its own docker-compose. Do not treat Kimball v2 as kimball-assess-erp.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000203",
        "name": "mirador-api operational map 2026-09-16",
        "repo": MIRADOR,
        "mentions": [MIRADOR, KAINAM_FRONT, XDA_AZURE, HACKETT_ORG],
        "content": """mirador-api (github.com/kainamAI/mirador-api, branch mirador-api-v2) is The Hackett Group AI application engine.

Purpose: SSE chat that turns prompts + user data into generated analytical apps / reports. Dual message store (legacy Conversation embed vs Message collection). Flow types: analytical_dashboard, report, interactive_experience.

How it runs: Docker Compose. App container PORT=3000 published as host 3001. Mongo service hostname mongodb, DB wallah. Swagger /docs. Prefix /api. ClerkAuthGuard global.

Modules (src/): chat (first-interaction/stream/edit SSE), flows, prompts, prompt (legacy), variables, ai-config, auth (Clerk), kimball (easy-import, table DDLs, pipeline link — backend-to-backend), senna (algorithm link), mcp (Streamable HTTP clients for Kimball/Monza), storage (inline Mongo or s3/azure), state-machine (XDA-315 app-creation, flags default off), access-query (read-only ClickHouse SELECT), data-viewer, templates, application-types, app-creation, context, metric-logic, security, health, schemas.

.env.example key names: ANTHROPIC_API_KEY, OPENAI_API_KEY, AZURE_FOUNDRY_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, OPENAI_API_VERSION, AZURE_TENANT_ID, AWS_DEFAULT_REGION, AWS_PROFILE, MONGO_URI, PORT, NODE_ENV, CORS_ORIGINS, CLICKHOUSE_URL, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_QUERY_TIMEOUT_MS, CLICKHOUSE_QUERY_MAX_RESULT_ROWS, CLICKHOUSE_QUERY_MAX_RESULT_BYTES, MIRADOR_MOCK_SCHEMA, EASY_IMPORT_DATA_READY_*, STORAGE_PROVIDER, AWS_REGION, AWS_S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_S3_ENDPOINT_URL, AWS_S3_FORCE_PATH_STYLE, AZURE_STORAGE_*, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, KAINAM_BASE_URL, KAINAM_API_KEY, KIMBALL_API_URL, KIMBALL_API_KEY, KIMBALL_REQUEST_TIMEOUT_MS, KIMBALL_RETRY_*, KIMBALL_CIRCUIT_BREAKER_*, KIMBALL_MCP_URL, MONZA_MCP_URL, MCP_REQUEST_TIMEOUT_MS, MCP_RETRY_*, STATE_MACHINE_CHAT_INTEGRATION, STATE_MACHINE_SMOKE_HANDLERS. Clerk keys are required in real deploys (CLERK_SECRET_KEY / CLERK_PUBLISHABLE_KEY) even if the example file omits them.

Infra: Mongo, optional ClickHouse (template_demo / mirador_mock), optional S3 or Azure Blob. Utz prod: https://mirador.utz.kainam.app/api. Hackett Backoffice reuses the same Clerk app.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000204",
        "name": "kimball-assess-erp operational map 2026-09-16",
        "repo": KIMBALL_ERP,
        "mentions": [KIMBALL_ERP, KIMBALL_TECH, WEB_UI, STUDIO, HACKETT_ORG],
        "content": """kimball-assess-erp (github.com/kainamAI/kimball-assess-erp) is the ERP-only Kimball Assess API.

Purpose: run governed assessment packs against ClickHouse assess schema; persist run metadata in Mongo assess_meta; optional FastMCP for KAI/studio agents. Not Kimball v2 pipeline API.

How it runs: FastAPI app/main.py. Default ASSESS_API_HOST=0.0.0.0 ASSESS_API_PORT=8300. CORS for local UI :3300. Auth ASSESS_AUTH_MODE=dev + ASSESS_API_KEY. Storage KIMBALL_ASSESS_STORAGE=local dir data/_assess.

Modules: app/api (HTTP), assess (run lifecycle), packs (assessment definitions), mcp (FastMCP stdio or HTTP :8310), sql, repositories, services, data, core.

.env.example key names: CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE=assess, CLICKHOUSE_BOOTSTRAP_DATABASE, CLICKHOUSE_SECURE, MONGO_URI, MONGO_DB=assess_meta, KIMBALL_ASSESS_STORAGE, KIMBALL_ASSESS_LOCAL_DIR, ASSESS_API_PORT, ASSESS_API_HOST, ASSESS_API_KEY, API_DEBUG, ASSESS_DEFAULT_CLIENT, ASSESS_DEFAULT_ACTOR, ASSESS_AUTH_MODE, ASSESS_DEV_ROLE, CORS_ORIGINS, KAI_MCP_ENABLED, KAI_MCP_ACTOR, KAI_MCP_ROLES, KAI_MCP_CLIENT, KAI_MCP_TRANSPORT, KAI_MCP_HOST, KAI_MCP_PORT, KAI_MCP_TIMEOUT_SEC.

Infra: ClickHouse :8123 DB assess; Mongo :27017 DB assess_meta. Distinct warehouse from Kainam Kimball default. web-ui assess proxy sends NEXT_PUBLIC_ASSESS_CLIENT / ACTOR / ROLES. Studio xda_assess_* tools can call this API.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000205",
        "name": "web-ui-aixelerator operational map 2026-09-16",
        "repo": WEB_UI,
        "mentions": [WEB_UI, WEB_UI_AIX, APP_API, STUDIO, HACKETT_ORG],
        "content": """web-ui-aixelerator is Abel's web_ui (Azure DevOps thehackettgroup/AIEXELERATOR V2 - CPMXPLR/web-ui, branch dev).

Purpose: AIX opportunity / discovery / XT / XDA consulting frontend. Final XDA UI ships in components/aix-v3/xda and app/(v3)/xda. Design system AI Innovation (aiinds). Clerk auth.

How it works: Next.js 16, React 19, RTK Query, v3 opportunity workspace. Same-origin proxies: /api/assess → Assess, /api/aix-proxy and appengine-proxy → app-api. OS URLs via NEXT_PUBLIC_OS_API_URL and NEXT_PUBLIC_OS_STUDIO_API_URL (lib/os-api-url.ts).

.env.example is almost empty. Real key names from code: NEXT_PUBLIC_API_AIXELERATOR_BASE_URL, NEXT_PUBLIC_API_AIXELERATOR_KEY, NEXT_PUBLIC_OS_API_URL, NEXT_PUBLIC_OS_STUDIO_API_URL, NEXT_PUBLIC_ASSESS_CLIENT, NEXT_PUBLIC_ASSESS_ACTOR, NEXT_PUBLIC_ASSESS_ROLES, NEXT_PUBLIC_USE_UI_MOCKS, NEXT_PUBLIC_XMS_LIVE, NEXT_PUBLIC_GOOGLE_TAG_MANAGER_ID, NEXT_PUBLIC_SURVEY_SECURITY_KEY, NEXT_PUBLIC_MICROSITE_CENTER_API_URL, NEXT_PUBLIC_MICROSITE_CENTER_CLIENT_ID, MICROSITE_CENTER_CLIENT_SECRET, NEXT_PUBLIC_AI_LANGFLOW_API_KEY, NEXT_PUBLIC_API_LANGFLOW_AXEL_INSIGHTS_URL, NEXT_PUBLIC_API_LANGFLOW_CHUNK_RESPONSE_URL, NEXT_PUBLIC_OPENAI_API_KEY, NEXT_PUBLIC_CHECKLIST_SURVEY_ID, NEXT_PUBLIC_SITE_URL, NEXT_PUBLIC_APP_URL, NEXT_PUBLIC_APP_VERSION, NEXT_PUBLIC_CLERK_SIGN_IN_URL, NEXT_PUBLIC_CLERK_SIGN_UP_URL, NEXT_PUBLIC_CLERK_ALLOWED_REDIRECT_ORIGINS, Clerk publishable/secret keys.

Major surfaces: aix-v3 opportunity dashboard, discovery chat, XT, XMS, XDA onboarding/intake, microsite, Axel insights, prompt library, backoffice configurations.

Infra: Vercel/Azure web; talks to app-api :3000 and studio :8000. Do not implement XDA in DIAL or XDA_V2.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000206",
        "name": "app-api-aixelerator operational map 2026-09-16",
        "repo": APP_API,
        "mentions": [APP_API, APP_API_AIX, WEB_UI, STUDIO, HACKETT_ORG],
        "content": """app-api-aixelerator is Abel's app-api (Azure AIEXELERATOR V2 - CPMXPLR/app-api, branch dev).

Purpose: NestJS 11 multi-tenant AIX API. Mongo/DocumentDB. Clerk JWT + hashed axk_live_ API keys. Swagger /api. Port 3000.

Auth stack: TenantExtractorMiddleware → RequireApiKeyGuard → ClerkAuthGuard → RetryThresholdInterceptor. Decorators @Public @RequireApiKey @RequirePermission @TenantId.

src/xda module: companies, roles (xda_roles), user roles, feature flags, app templates, canonical contracts C1-C30, flow mapping, app-engine, project entitlements, gateway, chat (upstream mirador), kainam, kimball bridge /api/xda/companies/:companyId/kimball/*, kimball-upload, ClickHouse helper, impersonation, bootstrap.

v1 modules include: discovery, discovery-items, discovery-flows, discovery-proposal, discovery-current-workplan, discovery-workplan-sections, discovery-current-workplan-economics, surveys, survey-config, session, session-assets, session-workflow, agent-custom, agent-instance, agent-arrangement, chain-execution, tools, execution-variable, prompt-store, unified-chat, chat-manager, rtm, rtm-sections, vendor-evaluation, competitive-landscape, tech-landscape, technologies, intelligence, intelligence-model, company-research, cfo-agenda, agenda, executives, industry-quals, catalog-data, analysis, settings, email, user-activity, public-entities, sdk-sections, testimonials, hackett-relations.

.env.example key names: NODE_ENV, MONGO_URI, CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY, XT_MIGRATION_SERVICE_EMAIL, XT_MIGRATION_CLERK_SECRET_KEY, XT_MIGRATION_TENANT_SLUG, ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_API_URL, SALESFORCE_API_KEY, SALESFORCE_API_URL, SALESFORCE_SYNC_ENABLED, SALESFORCE_SYNC_CRON, SALESFORCE_SYNC_TZ, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_DEPLOYMENT, OPENAI_API_VERSION, TAVILY_API_KEY, NESTJS_API_ENDPOINT, AI_LANGFLOW_API_KEY, PORT, CSF_API_DOMAIN, CSF_API_KEY, FORMBRICKS_API_KEY, FORMBRICKS_API_URL, FORMBRICKS_ENVIRONMENT_ID, PASSWORD_ENCRYPTION_KEY, MCP_CREDENTIAL_ENCRYPTION_KEY, MCP_INTERNAL_SHARED_SECRET, AWS_S3_BUCKET_NAME, LOGO_DEV_PUBLISHABLE_KEY, OS_API_URL, OS_STUDIO_API_URL.

Infra: Mongo/DocumentDB TLS (global-bundle.pem), pool 50. AWS Lambda/S3/SQS. OS_API_URL = aix-ai-api (sales intel, XT migration). OS_STUDIO_API_URL = studio (workplan-v6, process-flows, v1 chain). No silent fallback if studio URL unset.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000207",
        "name": "os-aixelerator-studio operational map 2026-09-16",
        "repo": STUDIO,
        "mentions": [STUDIO, APP_API, WEB_UI, KIMBALL_ERP, HACKETT_ORG],
        "content": """os-aixelerator-studio is the OneStream / AIX AI OS (FastAPI + LangGraph). Abel and Rafael share this folder name.

Purpose: long-running ReAct agents, document vectorization, OneStream MCP, workplans, XDA assess/curation tools, Atlas ingest. Postgres via DATABASE_URL. uvicorn port 8000.

Modules (app/modules): agent_harness (SSE executor, input_composer), agent_toolkit (xda_assess_engine/tools, xda_curation_*), agent_builder, agent_memory, agents, ai_core, ai_execution (xda_assess_assistant_agent), ai_opps, ai_routines, aix_mcp, application_analysis, artifact_library, asset_summarizer, atlas (ingest_router/service/repository), common, company_researcher, coupa, document_ingestion, document_vectorizer, HLM, knowledge_graph, metadata_builder, observability_reporting, onestream_client, onestream_docs, onestream_mcp (dm, sql, activity, execute, version, test_*), ontology_chat, oracle_converter, prerequisites, process_flows, prompt_workspace, recap_studio, requirements_agent, requirements_analysis, sales_intelligence, scoping, solution_platform, sow, tenant_vectorstore, tm1_catalog, user_stories_agent, vendor_evaluation, workflow_builder, workplan, workplan_v6, xml_constructor, xml_destroyer.

.env.example key names: AWS_PROFILE, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME (required, fail-fast), OPENAI_API_KEY, AIX_API_BASE_URL, AIX_EEA_API_KEY, AIX_OS_API_KEY, AIX_COUPA_API_KEY, AIX_SAP_API_KEY, AIX_XT_API_KEY, AIX_T2P_API_KEY, AIX_XDA_API_KEY, USE_HAKI, HAKI_API_BASE_URL, HAKI_API_KEY, HAKI_VECTORIZATION_JOB_ID, DOCUMENT_CHUNKS_TABLE, PINECONE_API_KEY, HUGGINGFACE_TOKEN, TAVILY_API_KEY, LANGCHAIN_TRACING_V2, LANGSMITH_API_KEY, LANGSMITH_ENDPOINT, LANGSMITH_PROJECT, PHOENIX_TRACING, PHOENIX_URL, PHOENIX_COLLECTOR_ENDPOINT, PHOENIX_PROJECT_NAME, PHOENIX_API_KEY, DATABASE_URL, AGENT_MEMORY_ENABLED, AGENT_MEMORY_EXTRACTION_ENABLED, AGENT_MEMORY_EXTRACTION_MODEL, AGENT_MEMORY_EXTRACTION_MIN_MESSAGES, AGENT_MEMORY_EXTRACTION_QUIET_SECONDS, AGENT_PROMPT_CACHE_ROLLING.

Tenant API keys are AIX_<SLUG>_API_KEY resolved in agent_harness/context.py; comma-delimited dev,prod axk_live_ keys. Phoenix traces LangGraph. S3 bucket os-aixelerator-studio. Prefer AWS CLI profile aixelerator over static keys.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000208",
        "name": "XDA Hackett Backoffice operational map 2026-09-16",
        "repo": XDA_AZURE,
        "mentions": [XDA_AZURE, MIRADOR, HACKETT_ORG],
        "content": """The Mac folder XDA is Azure DevOps thehackettgroup/XDA Hackett Backoffice (hackett-backoffice). It is not DIAL and not jallen40/XDA.

Purpose: Clerk-gated Hackett internal backoffice + client frontoffice around mirador-api, plus a small xda-api for XDA-specific Mongo.

Apps:
- apps/backoffice Next.js local :3000 (or :3003 if Kainam occupies 3000). Reads NEXT_PUBLIC_API_URL (not NEXT_PUBLIC_MIRADOR_API_URL). Users page merges Clerk directory (CLERK_SECRET_KEY) with mirador entitlements via MIRADOR_UPSTREAM_URL. Proxy keys: MIRADOR_PROXY_ENABLED, MIRADOR_ENTITLEMENTS_UPSTREAM_URL, MIRADOR_PROXY_ORIGIN, BACKOFFICE_PORT, APP_ORIGIN, REQUIRED_ORG_SLUG=xeq.
- apps/frontoffice Next.js :4000. NEXT_PUBLIC_MIRADOR_API_URL. Optional NEXT_PUBLIC_AIX_API_URL (server /api/aix-proxy). Optional NEXT_PUBLIC_KIMBALL_API_URL local escape hatch. XT Assistant POST /api/chat uses AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_BEARER_TOKEN_BEDROCK, AI_ASSISTANT_MODEL.
- apps/xda-api NestJS PORT=3010 HOST=0.0.0.0. MONGO_URI mongodb://localhost:27017/xda (separate from wallah). CLERK_SECRET_KEY, CLERK_PUBLISHABLE_KEY, ALLOWED_ORIGINS.

Shared rule: same Clerk keys on backoffice, frontoffice, and mirador-api so one login works. Local map: mirador-api Docker :3001, FO :4000, BO :3000/3003.

This clone is the Hackett Backoffice product. DIAL remains Abel's 50/50 XDA reference monorepo. Do not implement methodology engine here as if it were XDA_V2.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000209",
        "name": "XDA_V2 jallen40 operational map 2026-09-16",
        "repo": XDA_V2,
        "mentions": [XDA_V2, HACKETT_ORG],
        "content": """XDA_V2 is the clone of github.com/jallen40/XDA (Jeff Allen vanilla prototype, historically xda-ruby.vercel.app).

Purpose: consultant-led evidence engine reference — HDQRS, four plays, evidence ladder, browser-first processing. NOT the ship target. Final XDA ships in web-ui-aixelerator + app-api src/xda + studio tools.

How it works: no Node build, no package manager. Classic script IIFEs on global XDA, loaded by index.html. Tests are in-repo selftests XDA.<module>.selftest(). Serve via serve.ps1.

Config: js/config.js. supabase.url + supabase.anonKey (public by design). allowedEmailDomains thehackettgroup.com. Anthropic only through Supabase assist Edge Function — browser must not call api.anthropic.com. Never commit service_role. qa/clientfiles/ is gitignored.

Modules: js/canonical/* analysis engine, js/views*.js + js/canonical/views.js render, js/app.js router. A12 guard: pre-existing views must not reference XDA.canon inside render.

Infra: Supabase (RLS). Static hosting. Demo composites invariant 65, 65, 89, 78, 91.7, 48, 86.8.
""",
    },
    {
        "uuid": "8a1c0e20-9f31-4b6a-a111-000000000210",
        "name": "second-brain operational map 2026-09-16",
        "repo": SECOND_BRAIN,
        "mentions": [SECOND_BRAIN, HACKETT_ORG],
        "content": """second-brain is Rafael's Graphiti MCP knowledge graph used by Cursor/Claude.

Live Windows PC 192.168.15.2: Neo4j 5.26 :7474/:7687, MCP :8020, Ollama embeddings nomic-embed-text 768 cosine. Docker compose.remote.yml publishes LAN ports. POST /mcp returns 421 unless Host is 127.0.0.1:8020; Mac workaround scripts/mac-mcp-host-proxy.py or Cursor header.

.env.example key names: NEO4J_USER, NEO4J_PASSWORD, GRAPHITI_GROUP_ID, SEMAPHORE_LIMIT, LLM_TEMPERATURE, EXTRACTION_PAID_THRESHOLD, EXTRACTION_BURST_WINDOW_SEC, OLLAMA_MODEL_NAME, OLLAMA_API_URL, LLM_PROVIDER, MODEL_NAME, LLM_STRUCTURED_OUTPUT_MODE, OPENAI_API_KEY, OPENAI_API_URL, OPENAI_BASE_URL, ANTHROPIC_API_KEY, EMBEDDER_PROVIDER, EMBEDDER_MODEL, EMBEDDER_DIMENSIONS, EMBEDDER_API_URL.

Groups: global, software, hackett, aprendizaje, amonsolutions (from Abel Atenea backup); Mac also uses hackett-workspace, hackett-aixelerator, hackett-xda. Read tools take group_ids plural. add_memory is broken (reference_time). add_triplet EdgeDuplicate after first edge per group. Authoritative writes: Cypher MERGE Entity {uuid}.

Never store passwords, API keys, or .env values in memories — names and topology only.
""",
    },
]

MASTER = """Operational scan of Rafael Mac Hackett workspace on 2026-09-16. Key names only; no secret values.

Port map: kainam-front :3000; kai :8000; kimball v2 :8081; senna :8080; notifications :8085; platform_config :8003; mirador-api host :3001; assess :8300 (MCP :8310); studio :8000; app-api :3000; xda-api :3010; XDA frontoffice :4000; XDA backoffice :3000/3003; ClickHouse :8123; Mongo :27017; Redis :6379; second-brain Neo4j :7474/:7687 MCP :8020.

Config styles: kainam-front = runtime public/config.json. kainam-backend = per-service example.env. mirador-api / assess / studio / app-api / XDA apps = .env.example. web-ui = NEXT_PUBLIC_* in process.env. XDA_V2 = js/config.js. second-brain = .env for Neo4j/LLM/embedder.

Auth: Kainam products = Keycloak. AIX + Mirador + Hackett Backoffice = Clerk. Assess = ASSESS_API_KEY / dev mode. Studio→app-api = AIX_<SLUG>_API_KEY. XDA_V2 = Supabase RLS.

Do not mix: Kimball v2 :8081 ≠ kimball-assess-erp :8300. Mac folder XDA ≠ DIAL ≠ XDA_V2. Ship XDA in web-ui + app-api src/xda + studio.
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


def merge_edge(tx, source: str, target: str, name: str, fact: str, ep: str) -> None:
    edge_uuid = uid(f"{source}|{name}|{target}|ops")
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
        ep=ep,
    )


def write_episode(tx, ep_uuid: str, name: str, content: str, mentioned: list[str]) -> None:
    tx.run(
        """
        MERGE (e:Episodic {uuid: $uuid})
        SET e.name = $name,
            e.content = $content,
            e.group_id = $group,
            e.source = 'text',
            e.source_description = 'Rafael Mac repo operational scan 2026-09-16',
            e.created_at = $now,
            e.valid_at = $now,
            e.entity_edges = $edges
        """,
        uuid=ep_uuid,
        name=name,
        content=content,
        group=GROUP,
        now=NOW,
        edges=mentioned,
    )
    for target in mentioned:
        mention_uuid = uid(f"mention|{ep_uuid}|{target}")
        tx.run(
            """
            MATCH (e:Episodic {uuid: $ep})
            MATCH (n {uuid: $tid})
            MERGE (e)-[r:MENTIONS {uuid: $mu}]->(n)
            SET r.group_id = $group, r.created_at = $now
            """,
            ep=ep_uuid,
            tid=target,
            mu=mention_uuid,
            group=GROUP,
            now=NOW,
        )


def main() -> int:
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        print("Set NEO4J_PASSWORD", file=sys.stderr)
        return 2
    uri = os.environ.get("NEO4J_URI", "bolt://192.168.15.2:7687")
    driver = GraphDatabase.driver(uri, auth=("neo4j", password))
    try:
        with driver.session() as session:
            with session.begin_transaction() as tx:
                merge_entity(
                    tx,
                    SECOND_BRAIN,
                    "second-brain",
                    SUMMARIES[SECOND_BRAIN],
                    ["Repository"],
                )
                print("upserted second-brain")

                for node_uuid, summary in SUMMARIES.items():
                    tx.run(
                        """
                        MATCH (n {uuid: $uuid})
                        SET n.summary = $summary
                        """,
                        uuid=node_uuid,
                        summary=summary,
                    )
                    print("summary", node_uuid[-12:])

                all_mentioned = [HACKETT_ORG, SECOND_BRAIN]
                for ep in EPISODES:
                    write_episode(tx, ep["uuid"], ep["name"], ep["content"], ep["mentions"])
                    merge_edge(
                        tx,
                        ep["repo"],
                        HACKETT_ORG,
                        "BELONGS_TO",
                        "This Hackett workspace repository belongs to The Hackett Group.",
                        ep["uuid"],
                    )
                    print("episode", ep["name"])
                    all_mentioned.extend(ep["mentions"])

                write_episode(
                    tx,
                    MASTER_EP,
                    "Hackett workspace operational scan 2026-09-16",
                    MASTER,
                    list(dict.fromkeys(all_mentioned)),
                )
                print("master episode")
                tx.commit()

            rec = session.run(
                """
                MATCH (e:Episodic)
                WHERE e.uuid STARTS WITH '8a1c0e20-9f31-4b6a-a111-0000000002'
                RETURN e.name AS name
                ORDER BY e.name
                """
            )
            print("episodes:")
            for row in rec:
                print(" ", row["name"])
            n = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            print("nodes", n)
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
