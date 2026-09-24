# AGENTS.md — rules for working with the Second Brain

Give this file (or a summary) to every AI agent that uses the brain — as Cursor
Rules, a Claude Code `CLAUDE.md`, a system prompt, etc. The goal: knowledge
accumulates instead of being duplicated, and each agent benefits from what the
others learned.

The MCP server is named `second-brain`. Its main tools are: add a memory, search
facts, search nodes, and list episodes (the exact names are shown when you
connect, or via `scripts/test-brain.sh`). There is also `get_queue_status()`,
which reports how many episodes are still waiting (per group) after a burst of
`add_memory` calls — useful to confirm a batch finished processing before
searching for it.

---

## BEFORE an important task

1. **Search** the brain for anything related to the task.
2. For **The Hackett Group / XDA / AIX / Kainam / Mirador**, search the live
   graph with `group_ids: ["global", "software", "hackett"]`. That is the
   Atenea export imported on 2026-09-16 (Entity / Episodic / MENTIONS /
   RELATES_TO). Do not omit `group_ids` or you will only hit the default
   `global` slice.
3. Check **previous decisions** on the topic.
4. Check the **existing architecture** (servers, services, technologies).
5. Check **known problems** and their solutions.
6. Use that context so you don't repeat mistakes or re-decide settled things.

---

## AFTER an important task

1. Save the **decisions** you made (with the reason).
2. Save **new knowledge** (facts, non-secret configuration).
3. Save **solutions** to problems you fixed.
4. Save important **architecture changes**.
5. Relate the new info to existing entities — just write clear
   subject–verb–object sentences; Graphiti links same-named entities for you.

Write **atomic, natural-language** memories, e.g.:

> "Acme Corp uses Odoo 18 running in Docker on the server nova."

Graphiti extracts the entities (Acme Corp, Odoo, Docker, nova) and relationships
(uses, runs_on) automatically. You don't build the graph by hand.

---

## Groups (`group_id` / `group_ids`)

Write into the right group; when unsure use `global`. Since Graphiti's
`group_id` has no real hierarchy (it's just a string used as a filter),
simulate hierarchy with a name prefix: employer-scoped work under
`<employer>-`, personal projects under `personal-`, other companies under
`<company>-`. Example scheme (customize for yourself):

| group_id | For |
|---|---|
| `global` | Cross-cutting knowledge, about you, your machine, or the brain's own conventions |
| `<employer>-<project>` | Work for a specific employer, one group per project (e.g. `hackett-aixelerator`, `hackett-xda`) |
| `personal-<project>` | Personal projects |
| `<company>-<project>` | Projects for other companies/clients |

> ⚠️ **Parameter name differs between writing and reading, and there is no
> "search everything" default.** `add_memory` takes `group_id` (singular
> string). Every read tool — `get_episodes`, `search_nodes`,
> `search_memory_facts` — takes `group_ids` (**plural**, an array). Passing
> `group_id` to a read tool is silently ignored (no error), and omitting
> `group_ids` does **not** search across all groups — it falls back to the
> server's default group (`GRAPHITI_GROUP_ID` in `.env`, `global` by default).
> Since `global` usually holds almost nothing, this looks exactly like "the
> brain is empty" even though your data is intact. Always pass `group_ids`
> explicitly on reads, e.g. `group_ids: ["aixelerator"]`, or list every group
> you care about if you want a broad search.

---

## Extraction routing (`add_memory`)

`add_memory` queues work. The worker picks the LLM from burst size (episodes
enqueued in an 8-second window):

- **Fewer than 5** → local Ollama (`qwen2.5-brain`). Free.
- **5 or more** → the paid API in `.env` (`LLM_PROVIDER` / `MODEL_NAME`), if you
  configured one. Protects a CPU-only host on big dumps.

Embeddings always stay on Ollama. If you only run local Ollama, both paths are
local. Restarting the MCP **discards the in-memory queue**.

---

## Temporal memory

Graphiti versions facts over time: if something changes, **add a new memory**
instead of "correcting" it — the system marks the old one as past and knows which
is current. That lets you answer both "what does it use now?" and "what did it
use before?".

---

## NEVER store

- Passwords, API keys, tokens, secrets of any kind.
- Throwaway/ephemeral state with no lasting value.
- Whole conversations without summarizing.
- Duplicated info (search before you write).
- Other people's sensitive personal data.

If a fact is sensitive but useful, store the **fact, not the secret**:
"Service X needs an API key stored in the project's .env", never the value.
