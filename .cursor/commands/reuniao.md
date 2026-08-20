# Ingerir reunião no Second Brain

Vou te passar o resumo/notas de uma reunião (normalmente exportado do Granola).
Tua tarefa é salvá-lo no **second-brain** (MCP `second-brain`) como memórias
atômicas, seguindo estas regras.

## Antes de salvar
1. Se houver dúvida sobre algo já decidido, **busca no cérebro primeiro**
   (`search_memory_facts` / `search_nodes`) para não duplicar nem contradizer
   sem querer.
2. Identifica o **projeto** da reunião (ex.: SDA). Se for claramente de um
   projeto, usa esse nome como `group_id` (ex.: `sda`). Caso contrário, usa
   `work`.

## Como salvar
- Quebra a reunião em **memórias atômicas** — uma ideia por `add_memory`. Nunca
  despejes a transcrição inteira num só bloco.
- Cada memória é uma frase clara **sujeito–verbo–objeto**, na **mesma língua**
  do original. O Graphiti extrai as entidades e relações sozinho.
- **Inclui a data** da reunião no texto quando fizer diferença (ex.:
  "Na reunião de 2026-08-19, Juan decidiu ...").
- Cobre principalmente: **decisões** (com o porquê), **fatos/estado novo**,
  **problemas e soluções**, **mudanças de arquitetura** e **action items**
  (quem faz o quê).
- Se algo mudou em relação ao que já estava no cérebro, **adiciona uma memória
  nova** (não "corrige" a antiga) — o sistema versiona no tempo sozinho.

## NUNCA salvar
- Senhas, API keys, tokens ou segredos. Se um segredo for relevante, guarda o
  **fato, não o valor** ("o serviço X precisa de uma API key no .env").
- Fofoca / dados pessoais sensíveis de terceiros.
- Papo irrelevante ou estado efêmero sem valor duradouro.

## Depois
- Me mostra uma **lista curta** do que salvou (título de cada memória + o
  `group_id` usado).
- Lembra que a extração roda em Ollama local no CPU: o processamento é
  **assíncrono e pode levar alguns minutos** por memória. Os nós vão aparecer
  no grafo aos poucos.

---

**Resumo da reunião (colar abaixo):**
