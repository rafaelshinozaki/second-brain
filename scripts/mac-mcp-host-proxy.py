#!/usr/bin/env python3
"""Local Host-header rewrite so Cursor on the Mac can talk to Graphiti.

Graphiti/uvicorn on the Windows PC accepts Host: 127.0.0.1:8020 and
Host: localhost:8020, but returns 421 Invalid Host header for
Host: 192.168.15.2:8020 — which is what Cursor sends for the LAN URL.

Listen on 127.0.0.1:18020 and forward to 192.168.15.2:8020 with the
accepted Host. Then point Cursor at http://127.0.0.1:18020/mcp

  python3 scripts/mac-mcp-host-proxy.py
"""
from __future__ import annotations

import asyncio

LISTEN = ("127.0.0.1", 18020)
UPSTREAM = ("192.168.15.2", 8020)
REWRITE_HOST = "127.0.0.1:8020"


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


def _rewrite_host(first: bytes) -> bytes:
    text = first.decode("latin1")
    lines = text.split("\r\n")
    out = []
    rewrote = False
    for line in lines:
        if line.lower().startswith("host:"):
            out.append(f"Host: {REWRITE_HOST}")
            rewrote = True
        else:
            out.append(line)
    if not rewrote and out:
        out.insert(1, f"Host: {REWRITE_HOST}")
    return "\r\n".join(out).encode("latin1")


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        up_r, up_w = await asyncio.open_connection(*UPSTREAM)
    except OSError as exc:
        writer.close()
        await writer.wait_closed()
        print(f"upstream {UPSTREAM} failed: {exc}", flush=True)
        return
    first = await reader.read(65536)
    if not first:
        up_w.close()
        writer.close()
        return
    up_w.write(_rewrite_host(first))
    await up_w.drain()
    await asyncio.gather(_pipe(reader, up_w), _pipe(up_r, writer))


async def main() -> None:
    server = await asyncio.start_server(handle, *LISTEN)
    print(f"MCP host proxy {LISTEN[0]}:{LISTEN[1]} -> {UPSTREAM[0]}:{UPSTREAM[1]} Host={REWRITE_HOST}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
