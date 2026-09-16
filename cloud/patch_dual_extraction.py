#!/usr/bin/env python3
"""Bake dual extraction routing (Ollama vs paid API) into the Graphiti MCP image.

Copies our queue worker and extraction router, then patches graphiti_mcp_server.py
and factories.py so add_memory picks local Ollama for small bursts and the
configured LLM_PROVIDER for dumps of 5+ episodes.

Idempotent. Best-effort on factories (build still succeeds). The MCP server
patches are required — we exit 1 if those anchors are missing so a silent
upstream drift cannot ship a build that claims to route but does not.
"""
from __future__ import annotations

import sys
from pathlib import Path

MCP = Path('/app/mcp/src')
SERVER = MCP / 'graphiti_mcp_server.py'
FACTORIES = MCP / 'services' / 'factories.py'


def _replace_once(src: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if new.strip() and new in src and old not in src:
        print(f'[patch_dual_extraction] {label}: already applied')
        return src, True
    if old not in src:
        print(f'[patch_dual_extraction] WARNING: {label} anchor not found')
        return src, False
    return src.replace(old, new, 1), True


def patch_factories(src: str) -> str:
    if 'def create_ollama_from_env' in src:
        print('[patch_dual_extraction] factories: create_ollama_from_env already present')
        return src

    marker = 'class EmbedderFactory:'
    helper = '''    @staticmethod
    def create_ollama_from_env() -> LLMClient:
        """Local Ollama chat client (OpenAI-compatible) for small-burst extraction."""
        import logging
        import os

        from graphiti_core.llm_client.config import LLMConfig as CoreLLMConfig
        from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient

        logger = logging.getLogger(__name__)
        model = os.getenv('OLLAMA_MODEL_NAME', 'qwen2.5-brain')
        # Prefer an explicit Ollama URL. Do NOT fall back to OPENAI_API_URL —
        # that may already point at Gemini/OpenAI when LLM_PROVIDER is paid.
        base_url = (
            os.getenv('OLLAMA_API_URL')
            or os.getenv('EMBEDDER_API_URL')
            or 'http://host.docker.internal:11434/v1'
        )
        try:
            temperature = float(os.getenv('OLLAMA_TEMPERATURE', '0'))
        except ValueError:
            temperature = 0.0
        max_tokens = int(os.getenv('OLLAMA_MAX_TOKENS', '4096'))

        logger.info(f'Creating Ollama LLM client model={model} base_url={base_url}')
        llm_config = CoreLLMConfig(
            api_key=os.getenv('OLLAMA_API_KEY', 'ollama'),
            base_url=base_url,
            model=model,
            small_model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return OpenAIGenericClient(config=llm_config)


'''
    if marker not in src:
        print('[patch_dual_extraction] WARNING: EmbedderFactory marker not found')
        return src
    print('[patch_dual_extraction] factories: adding create_ollama_from_env')
    return src.replace(marker, helper + marker, 1)


def patch_server(src: str) -> tuple[str, int]:
    if 'async def add_episode_routed' in src:
        print('[patch_dual_extraction] graphiti_mcp_server.py already patched')
        return src, 9

    ok = 0

    src, applied = _replace_once(
        src,
        'from services.factories import (\n'
        '    CrossEncoderFactory,\n'
        '    DatabaseDriverFactory,\n'
        '    EmbedderFactory,\n'
        '    LLMClientFactory,\n'
        ')\n'
        'from services.queue_service import QueueService\n',
        'from services.extraction_router import describe as describe_extraction_route\n'
        'from services.factories import (\n'
        '    CrossEncoderFactory,\n'
        '    DatabaseDriverFactory,\n'
        '    EmbedderFactory,\n'
        '    LLMClientFactory,\n'
        ')\n'
        'from services.queue_service import QueueService\n',
        'imports',
    )
    ok += int(applied)

    src, applied = _replace_once(
        src,
        '        self.client: Graphiti | None = None\n',
        '        self.client: Graphiti | None = None\n'
        '        self.llm_paid = None\n'
        '        self.llm_ollama = None\n'
        '        self.llm_lock = asyncio.Lock()\n',
        'GraphitiService.__init__',
    )
    ok += int(applied)

    src, applied = _replace_once(
        src,
        '            # Create LLM client based on configured provider\n'
        '            try:\n'
        '                llm_client = LLMClientFactory.create(self.config.llm)\n'
        '            except Exception as e:\n'
        "                logger.warning(f'Failed to create LLM client: {e}')\n",
        '            # Create LLM client based on configured provider (paid / default)\n'
        '            try:\n'
        '                llm_client = LLMClientFactory.create(self.config.llm)\n'
        '            except Exception as e:\n'
        "                logger.warning(f'Failed to create LLM client: {e}')\n"
        '\n'
        '            self.llm_paid = llm_client\n'
        '            try:\n'
        '                self.llm_ollama = LLMClientFactory.create_ollama_from_env()\n'
        '                logger.info(\n'
        "                    'Ollama extraction fallback ready: '\n"
        '                    f\'{os.getenv("OLLAMA_MODEL_NAME", "qwen2.5-brain")} @ \'\n'
        '                    f\'{os.getenv("OLLAMA_API_URL") or os.getenv("EMBEDDER_API_URL") or "host.docker.internal:11434"}\'\n'
        '                )\n'
        '            except Exception as e:\n'
        "                logger.warning(f'Failed to create Ollama LLM client: {e}')\n"
        '                self.llm_ollama = None\n',
        'dual LLM clients',
    )
    ok += int(applied)

    src, applied = _replace_once(
        src,
        "                    f'Using LLM provider: {self.config.llm.provider} / {self.config.llm.model}'\n",
        "                    f'Using paid LLM provider: {self.config.llm.provider} / {self.config.llm.model}'\n",
        'paid LLM log',
    )
    ok += int(applied)

    src, applied = _replace_once(
        src,
        "                logger.info('No LLM client configured - entity extraction will be limited')\n",
        "                logger.info('No paid LLM client configured - entity extraction will be limited')\n"
        "            logger.info(f'Extraction routing: {describe_extraction_route()}')\n",
        'routing log',
    )
    ok += int(applied)

    routed_method = '''
    async def add_episode_routed(self, route: str, **kwargs) -> None:
        """Run add_episode with Ollama or the paid LLM, serialized on llm_lock.

        Graphiti holds a single llm_client. Extraction reads clients.llm_client,
        so both fields are swapped under a lock.
        """
        client = await self.get_client()
        if route == 'ollama' and self.llm_ollama is not None:
            llm = self.llm_ollama
            label = f'ollama/{os.getenv("OLLAMA_MODEL_NAME", "qwen2.5-brain")}'
        else:
            if route == 'ollama' and self.llm_ollama is None:
                logger.warning('Ollama extraction unavailable; falling back to paid API')
            llm = self.llm_paid or client.llm_client
            label = f'paid/{self.config.llm.provider}/{self.config.llm.model}'

        async with self.llm_lock:
            client.llm_client = llm
            client.clients.llm_client = llm
            logger.info(
                f'Extraction route={route} ({label}) '
                f'episode={kwargs.get("name")} group={kwargs.get("group_id")}'
            )
            await client.add_episode(**kwargs)

'''

    src, applied = _replace_once(
        src,
        '            raise RuntimeError(\'Failed to initialize Graphiti client\')\n'
        '        return self.client\n\n\n@mcp.tool()\nasync def add_memory(\n',
        '            raise RuntimeError(\'Failed to initialize Graphiti client\')\n'
        '        return self.client\n'
        + routed_method
        + '\n@mcp.tool()\nasync def add_memory(\n',
        'add_episode_routed',
    )
    ok += int(applied)

    src, applied = _replace_once(
        src,
        '            message=f"Episode \'{name}\' queued for processing in group \'{effective_group_id}\'"\n',
        '            message=(\n'
        '                f"Episode \'{name}\' queued for processing in group \'{effective_group_id}\' "\n'
        "                f'({describe_extraction_route()})'\n"
        '            )\n',
        'add_memory message',
    )
    ok += int(applied)

    src, applied = _replace_once(
        src,
        "            message=f'Graphiti MCP server is running and connected to {provider_name} database',\n",
        '            message=(\n'
        "                f'Graphiti MCP server is running and connected to {provider_name} database. '\n"
        "                f'{describe_extraction_route()}'\n"
        '            ),\n',
        'get_status message',
    )
    ok += int(applied)

    src, applied = _replace_once(
        src,
        '    await queue_service.initialize(graphiti_client)\n',
        '    await queue_service.initialize(graphiti_client, graphiti_service)\n',
        'queue initialize',
    )
    ok += int(applied)

    return src, ok


def main() -> int:
    router = MCP / 'services' / 'extraction_router.py'
    queue = MCP / 'services' / 'queue_service.py'
    if not router.exists() or not queue.exists():
        print('[patch_dual_extraction] ERROR: extraction_router.py / queue_service.py '
              'must be COPY’d into the image before this patch runs')
        return 1

    if FACTORIES.exists():
        FACTORIES.write_text(patch_factories(FACTORIES.read_text()))
    else:
        print(f'[patch_dual_extraction] WARNING: {FACTORIES} missing')

    if not SERVER.exists():
        print(f'[patch_dual_extraction] ERROR: {SERVER} missing')
        return 1

    patched, ok = patch_server(SERVER.read_text())
    SERVER.write_text(patched)
    print(f'[patch_dual_extraction] graphiti_mcp_server.py: {ok}/9 anchors applied')
    if ok < 8:
        print('[patch_dual_extraction] ERROR: too many anchors missed; upstream image changed?')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
