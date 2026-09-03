#!/usr/bin/env python3
# Smoke test for the Second Brain over the real MCP protocol (streamable HTTP).
# Lists the real tools, inserts two related memories, and searches them back.
# Run with:  bash scripts/test-brain.sh
import argparse
import asyncio
import os
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = os.environ.get("MCP_URL", "http://127.0.0.1:8020/mcp/")
GROUP = "smoke-test"


def text_of(result):
    return "\n".join(getattr(c, "text", str(c)) for c in (getattr(result, "content", []) or []))


async def call(session, name, args, show=1200):
    print(f"\n-> {name}({args})")
    body = text_of(await session.call_tool(name, args))
    print(body[:show])
    return body


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search-only", action="store_true",
                    help="only search (e.g. to prove another agent can read the data)")
    ap.add_argument("--wait", type=int, default=1200,
                    help="max seconds to wait for async processing")
    args = ap.parse_args()

    async with streamable_http_client(URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = [t.name for t in (await session.list_tools()).tools]
            print("=== REAL MCP TOOLS ===")
            for t in tools:
                print(f"  - {t}")

            ok_erp = ok_run = False

            if not args.search_only:
                await call(session, "add_memory", {
                    "name": "Company ERP",
                    "episode_body": "Acme Corp uses Odoo as its ERP.",
                    "group_id": GROUP, "source": "text",
                    "source_description": "smoke test"})
                await call(session, "add_memory", {
                    "name": "Odoo runtime",
                    "episode_body": "Odoo runs on Docker on the server called nova.",
                    "group_id": GROUP, "source": "text",
                    "source_description": "smoke test"})

                print(f"\n... waiting for async processing (up to {args.wait}s) ...")
                deadline = time.time() + args.wait
                while time.time() < deadline:
                    await asyncio.sleep(20)
                    nb = text_of(await session.call_tool(
                        "search_nodes", {"query": "Odoo Docker",
                                         "group_ids": [GROUP], "max_nodes": 10}))
                    if "docker" in nb.lower():
                        print("   nodes extracted ✓")
                        break

            print("\n=== Q1: What ERP does the company use? ===")
            b = await call(session, "search_memory_facts",
                           {"query": "What ERP does the company use?",
                            "group_ids": [GROUP], "max_facts": 10})
            ok_erp = "odoo" in b.lower()

            print("\n=== Q2: Where does Odoo run? ===")
            b = await call(session, "search_memory_facts",
                           {"query": "Where does Odoo run?",
                            "group_ids": [GROUP], "max_facts": 10})
            ok_run = "docker" in b.lower()

            print("\n=== SUMMARY ===")
            print("ERP found (Odoo):   ", "PASS" if ok_erp else "FAIL")
            print("Runtime found (Docker):", "PASS" if ok_run else "FAIL")
            return ok_erp and ok_run


if __name__ == "__main__":
    sys.exit(0 if asyncio.run(main()) else 2)
