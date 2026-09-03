#!/usr/bin/env python3
"""Patch graphiti-mcp's LLM factory so the `openai` provider uses the Chat
Completions API instead of the Responses API.

The upstream `openai` client calls `client.responses.parse(...)` (the OpenAI
Responses API). Most OpenAI-compatible endpoints — Gemini's OpenAI endpoint,
older Ollama, LM Studio, vLLM, … — only implement `/chat/completions` and return
404 on `/responses`. Graphiti ships `OpenAIGenericClient`, which uses
`/chat/completions`; this patch makes the `openai` provider use it, and passes
the configured `base_url` through.

Best-effort: if the code has changed and a block isn't found, we print a warning
and exit 0 so the Docker build still succeeds.
"""
import sys

PATH = "/app/mcp/src/services/factories.py"

OLD_CFG = """                llm_config = CoreLLMConfig(
                    api_key=api_key,
                    model=config.model,
                    small_model=small_model,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )"""
NEW_CFG = """                llm_config = CoreLLMConfig(
                    api_key=api_key,
                    base_url=config.providers.openai.api_url,  # PATCH: endpoint (Ollama/Gemini/OpenAI)
                    model=config.model,
                    small_model=small_model,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )"""

OLD_RET = """                # Check if this is a reasoning model (o1, o3, gpt-5 family)
                reasoning_prefixes = ('o1', 'o3', 'gpt-5')
                is_reasoning_model = config.model.startswith(reasoning_prefixes)

                # Only pass reasoning/verbosity parameters for reasoning models (gpt-5 family)
                if is_reasoning_model:
                    return OpenAIClient(config=llm_config, reasoning='minimal', verbosity='low')
                else:
                    # For non-reasoning models, explicitly pass None to disable these parameters
                    return OpenAIClient(config=llm_config, reasoning=None, verbosity=None)"""
NEW_RET = """                # PATCH: use the generic client (Chat Completions API) so any
                # OpenAI-compatible endpoint that lacks the Responses API works
                # (Gemini's OpenAI endpoint, older Ollama, LM Studio, ...).
                from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
                return OpenAIGenericClient(config=llm_config)"""


def main() -> int:
    try:
        src = open(PATH).read()
    except FileNotFoundError:
        print(f"[patch_factories] WARNING: {PATH} not found; skipping.")
        return 0

    if "OpenAIGenericClient(config=llm_config)" in src:
        print("[patch_factories] already patched.")
        return 0

    changed = 0
    if OLD_CFG in src:
        src = src.replace(OLD_CFG, NEW_CFG, 1); changed += 1
    else:
        print("[patch_factories] WARNING: llm_config block not found (base_url).")
    if OLD_RET in src:
        src = src.replace(OLD_RET, NEW_RET, 1); changed += 1
    else:
        print("[patch_factories] WARNING: openai return block not found (generic client).")

    if changed:
        open(PATH, "w").write(src)
        print(f"[patch_factories] applied {changed}/2 edits.")
    else:
        print("[patch_factories] WARNING: nothing patched — upstream image may have changed. "
              "Cloud endpoints without the Responses API (e.g. Gemini) may 404; see README.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
