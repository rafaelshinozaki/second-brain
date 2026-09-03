# AI Second Brain — MCP image with cloud-LLM fixes baked in.
#
# Built automatically by `docker compose up -d --build`. It patches two rough
# edges of the upstream `zepai/knowledge-graph-mcp:standalone` image so that
# ANY extraction model works out of the box:
#
#   1. Installs the Anthropic SDK (missing in the base image) so the native
#      `anthropic` provider works — required for Claude.
#   2. Makes the `openai` provider call the Chat Completions API
#      (/chat/completions) instead of the Responses API (/responses). Most
#      OpenAI-compatible endpoints (Gemini, older Ollama, LM Studio, …) do NOT
#      implement /responses and would 404 otherwise.
#   3. Routes small add_memory bursts to local Ollama and 5+ episode dumps to
#      the paid LLM_PROVIDER so a CPU box is not crushed (and you save money).
#
# The Chat Completions patch is best-effort: if the upstream image changes and
# the patch can't apply, the build still succeeds (Claude keeps working; see
# README troubleshooting). Dual-extraction patches fail the build if anchors
# are missing so a silent drift cannot ship a router that does not route.

FROM zepai/knowledge-graph-mcp:standalone

# 1) Claude / Anthropic native provider
RUN cd /app/mcp && uv pip install anthropic

# 2) OpenAI provider -> Chat Completions API (works with all compat endpoints)
COPY cloud/patch_factories.py /tmp/patch_factories.py
RUN /app/mcp/.venv/bin/python /tmp/patch_factories.py

# 3) Dual extraction: small bursts stay on local Ollama; 5+ use LLM_PROVIDER
COPY config/extraction_router.py /app/mcp/src/services/extraction_router.py
COPY config/queue_service.py /app/mcp/src/services/queue_service.py
COPY cloud/patch_dual_extraction.py /tmp/patch_dual_extraction.py
RUN /app/mcp/.venv/bin/python /tmp/patch_dual_extraction.py
