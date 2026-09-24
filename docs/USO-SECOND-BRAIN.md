# Second Brain — guia de uso (setup do Rafael)

Guia da **nossa** instalação: o que já foi montado, como o **PC Windows** roda o
cérebro (servidor) e como o **Mac** (ou qualquer máquina da rede) usa como
**cliente**. Para a documentação genérica do projeto, veja o [`README.md`](../README.md).

> **Modelo mental:** o cérebro (Neo4j + Graphiti MCP + Ollama) roda **só no PC
> Windows**. O Mac **não** sobe Docker nem tem cópia dos dados — ele apenas
> **conecta via MCP** pela rede local e lê/escreve memórias no cérebro do PC.

---

## Estado atual (o que já fizemos)

- **Servidor:** PC Windows (`192.168.15.2` na LAN). Roda dois containers
  (`second-brain-neo4j`, `second-brain-mcp`) com `restart: unless-stopped` — sobem
  sozinhos no boot — mais o **Ollama nativo** (extração + embeddings no CPU/GPU).
- **Extração:** local no Ollama (`qwen2.5-brain` + `nomic-embed-text`),
  assíncrona (pode levar minutos por memória; não bloqueia o agente).
- **Acesso remoto habilitado:** as portas foram publicadas na LAN via
  `docker-compose.remote.yml`. A imagem upstream do Graphiti MCP **já escuta
  `0.0.0.0`** — o patch antigo de `host='0.0.0.0'` documentado neste repo **não
  foi necessário**. Firewall do Windows liberado nas portas `8020/7474/7687`
  **só para a sub-rede `192.168.15.x`** (nada exposto à internet).
- **Host header (Mac → Cursor):** `/health` aceita `Host: 192.168.15.2:8020`,
  mas `POST /mcp` devolve `421 Invalid Host header`. O uvicorn/Starlette só
  aceita `Host: 127.0.0.1:8020` ou `Host: localhost:8020`. No Mac, o
  `~/.cursor/mcp.json` manda `"headers": { "Host": "127.0.0.1:8020" }` junto
  da URL `http://192.168.15.2:8020/mcp`. Se o Cursor ignorar o header, rode
  `python3 scripts/mac-mcp-host-proxy.py` e aponte o MCP para
  `http://127.0.0.1:18020/mcp`.
- **Backup automático:** tarefa agendada no Windows (`SecondBrainBackup`, diária
  03:15) via `scripts/backup.ps1` → dumps em `./backups` (retenção 14 dias).
- **Regras para agentes:** `AGENTS.md` (na raiz) define o protocolo
  *ler-antes / escrever-depois*. Vários repos do ecossistema têm
  `.cursor/rules/second-brain.mdc` apontando pro mesmo cérebro (grupo `aixelerator`).
- **Comando `/reuniao`:** versionado em [`.cursor/commands/reuniao.md`](../.cursor/commands/reuniao.md)
  — cola as notas do Granola e ele salva como memórias atômicas.
- **Fonte Hackett / XDA (a partir de 2026-09-16):** o export lógico da Atenea
  (`backups/hackett-xda-current`) foi **importado no Neo4j vivo** do PC
  Windows via `scripts/import-hackett-backup.py` (MERGE por `uuid`,
  idempotente). 748 nós + 2213 arestas: `Episodic`, `Entity` tipados
  (Person, Organization, Project, Repository, …), `MENTIONS` e `RELATES_TO`.
  Grupos: `global`, `software`, `hackett`, `aprendizaje`, `amonsolutions`.
  Busque no MCP com `group_ids: ["global","software","hackett"]`. Reimportar:

  ```bash
  NEO4J_URI=bolt://192.168.15.2:7687 NEO4J_PASSWORD=... \
    python3 scripts/import-hackett-backup.py
  ```

### Grupos (`group_id`) em uso

Reorganizado em 02/09/2026: como o Graphiti não tem hierarquia real de grupos
(`group_id` é só uma string usada como filtro), a hierarquia é simulada por
convenção de prefixo. Trabalho do The Hackett Group usa `hackett-`; projetos
pessoais usam `personal-`; projetos de outra empresa usam o nome dela.

| group_id | Para |
|---|---|
| `global` | Conhecimento transversal, sobre você/a máquina, e a própria convenção de grupos |
| `hackett-aixelerator` | Ecossistema Aixelerator / AIX / Kainam / Mirador (The Hackett Group) |
| `hackett-xda` | Achados e reuniões específicas do projeto XDA (The Hackett Group) |
| `hackett-workspace` | Mapa dos repos do Mac e a relação de dono com The Hackett Group |
| `hackett-avira-health` | Projeto Avira Health (The Hackett Group) |
| `personal-<projeto>` | Projetos pessoais |
| `<empresa>-<projeto>` | Projetos de outras empresas |

Para "conectar" assuntos entre grupos relacionados na busca, passe todos os
`group_ids` desejados explicitamente (ex.: `["hackett-aixelerator", "hackett-xda"]`)
— não existe busca automática cruzando grupos.

Na dúvida, use `global`.

> ⚠️ **`group_id` (escrita) vs `group_ids` (leitura) — não existe "buscar em
> tudo" implícito.** O `add_memory` usa `group_id` (singular). Já `get_episodes`,
> `search_nodes` e `search_memory_facts` usam `group_ids` (**plural, lista**) —
> mandar `group_id` nessas ferramentas é **ignorado silenciosamente**. Omitir
> `group_ids` **não** busca em todos os grupos: cai no grupo default do servidor
> (`GRAPHITI_GROUP_ID`, `global` por padrão), que normalmente tem quase nada —
> então uma leitura sem `group_ids` parece "cérebro vazio" mesmo com os dados
> intactos. Sempre passe `group_ids` explicitamente, ex.: `group_ids: ["aixelerator"]`.

---

## Usar do Mac (cliente)

Pré-requisitos: Mac na **mesma rede** do PC (faixa `192.168.15.x`) e o PC ligado
com o cérebro no ar.

### 1. Testar se enxerga o cérebro

```bash
curl http://192.168.15.2:8020/health
# esperado: {"status":"healthy","service":"graphiti-mcp"}
```

Se der timeout, veja [Rede não conecta](#rede-nao-conecta) no fim.

### 2. Cursor

Se você **abrir este repo clonado** no Cursor, o arquivo de projeto
[`.cursor/mcp.json`](../.cursor/mcp.json) já configura o servidor `second-brain`
automaticamente — nada a fazer.

Para deixar o cérebro disponível em **qualquer** projeto do Mac, adicione também
ao global `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "second-brain": {
      "url": "http://192.168.15.2:8020/mcp",
      "headers": { "Host": "127.0.0.1:8020" }
    }
  }
}
```

Recarregue o Cursor e confira em **Settings → MCP**. O endpoint é **sem barra no
final** (`/mcp`, não `/mcp/`). O `Host` reescrito é obrigatório: sem ele o
`POST /mcp` responde `421 Invalid Host header`.

### 3. Claude Code

```bash
claude mcp add --transport http second-brain http://192.168.15.2:8020/mcp
```

### 4. Neo4j Browser (opcional, ver o grafo)

Abra `http://192.168.15.2:7474`, conecte em `bolt://192.168.15.2:7687`, usuário
`neo4j`. A senha está no `.env` **do PC** (não vem no clone — `.env` é
git-ignored). Copie de lá quando precisar.

### 5. Como o agente deve usar o cérebro

Vale para Mac e PC. O `AGENTS.md` já instrui os agentes, em resumo:

- **Antes** de uma tarefa importante: buscar no cérebro
  (`search_memory_facts` / `search_nodes`) decisões, arquitetura e problemas já
  conhecidos.
- **Depois**: salvar o que é durável com `add_memory` — decisões (com o porquê),
  fatos/arquitetura novos, soluções. Frases **atômicas**, uma ideia por memória,
  na língua da fonte. Se algo mudou, **adicione** memória nova (não reescreva a
  antiga — o grafo versiona no tempo).
- **Nunca** salvar senhas/tokens/segredos — guarde o *fato*, não o *valor*.
- Para reuniões, use o comando **`/reuniao`**.

---

## Operar o servidor (no PC Windows)

O acesso remoto exige subir o stack com **os dois** arquivos de compose:

```powershell
docker compose -f docker-compose.yml -f docker-compose.remote.yml up -d
```

> ⚠️ Se rodar só `docker compose up -d` (sem o `docker-compose.remote.yml`), o
> cérebro volta a ser **localhost-only** e o Mac perde o acesso. Reboot e o
> backup diário (que usa `stop`/`start`) **preservam** o acesso remoto — só o
> `up` sem o override é que reverte.

Comandos úteis:

```powershell
docker compose ps                              # status
docker compose logs -f graphiti-mcp            # logs do MCP / extração
curl.exe http://127.0.0.1:8020/health          # saúde local
Start-ScheduledTask -TaskName SecondBrainBackup   # backup manual agora
pwsh -File scripts\backup.ps1                   # backup manual (direto)
```

### Reabilitar acesso remoto do zero (se precisar)

Se o arquivo com patch sumir ou a config resetar:

1. A imagem upstream **já escuta `0.0.0.0`** — não reaplique o patch antigo de
   `host='0.0.0.0'`. Extraia o arquivo só se precisar recolocar a tool
   `get_queue_status` (não sobrevive a essa regeneração, já que o arquivo é
   git-ignored):
   ```powershell
   docker cp second-brain-mcp:/app/mcp/src/graphiti_mcp_server.py config/graphiti_mcp_server.py
   ```
   Cole o snippet abaixo logo antes de
   `@mcp.custom_route('/health', methods=['GET'])`, no mesmo arquivo
   `config/graphiti_mcp_server.py`.
   ```python
   @mcp.tool()
   async def get_queue_status() -> StatusResponse:
       """Get how many episodes are still pending processing, per group_id.

       'Pending' counts episodes waiting in the queue (not yet picked up by the
       worker). If a group's worker is currently running, one additional episode
       is being processed right now on top of that count.
       """
       global queue_service

       if queue_service is None:
           return StatusResponse(status='error', message='Queue service not initialized')

       try:
           group_ids = sorted(queue_service._episode_queues.keys())
           if not group_ids:
               return StatusResponse(
                   status='ok',
                   message='No episodes have been queued since the server last started.',
               )

           total_waiting = 0
           parts = []
           for group_id in group_ids:
               waiting = queue_service.get_queue_size(group_id)
               running = queue_service.is_worker_running(group_id)
               total_waiting += waiting
               parts.append(
                   f"{group_id}: {waiting} waiting"
                   + (' + 1 processing now' if running else ' (worker idle)')
               )

           return StatusResponse(
               status='ok',
               message=f'{total_waiting} episode(s) waiting across all groups. ' + '; '.join(parts),
           )
       except Exception as e:
           error_msg = str(e)
           logger.error(f'Error reading queue status: {error_msg}')
           return StatusResponse(status='error', message=f'Error reading queue status: {error_msg}')
   ```
   Depois de colar, `docker compose restart graphiti-mcp` já aplica (o arquivo é
   bind-mounted, não precisa rebuild).
2. Confirmar `docker-compose.remote.yml` publicando em `192.168.15.2`. O volume
   do `graphiti_mcp_server.py` só é necessário se você reaplicou
   `get_queue_status`.
3. Firewall (uma vez, como Administrador): `scripts\enable-remote-firewall.ps1`.
4. Subir com os dois compose (comando acima).

---

## Se o IP do PC mudar

`192.168.15.2` vem por **DHCP**. Se o roteador der outro IP, o container pode
falhar ao subir e o Mac perde o endereço. Soluções:

- **Recomendado:** criar uma **reserva de DHCP** no roteador fixando esse PC em
  `192.168.15.2`.
- Se o IP mudar mesmo assim, atualize o novo IP em `docker-compose.remote.yml`,
  `.cursor/mcp.json` e no `~/.cursor/mcp.json` do Mac, e suba de novo.

---

## Rede não conecta

Se `curl http://192.168.15.2:8020/health` falhar do Mac:

- Confirme que o Mac está na **mesma sub-rede** (`192.168.15.x`) e no **mesmo
  roteador** — não numa Wi-Fi de convidados isolada.
- Confirme no PC que o stack subiu com o `docker-compose.remote.yml`
  (`docker ps` deve mostrar `192.168.15.2:8020->8020/tcp`).
- Confirme as regras de firewall no PC:
  `Get-NetFirewallRule -DisplayName 'Second Brain*'`.
- Endpoint MCP é **sem barra final** (`/mcp`).
- Se `/health` funcionar mas o Cursor ficar vermelho: é o `421 Invalid Host
  header` em `POST /mcp`. Confira o `headers.Host` no `mcp.json` ou use
  `scripts/mac-mcp-host-proxy.py`.
- Escrita no grafo (imagem atual): `add_memory` falha com
  `QueueService.add_episode() unexpected keyword argument 'reference_time'`.
  `add_triplet` grava a **primeira** aresta de um `group_id` e depois quebra
  com `EdgeDuplicate`. Mapa completo dos repos está no grupo
  `hackett-workspace` (uma fact `OWNS_WORKSPACE`).

> 🔒 O MCP **não tem autenticação própria**. Só está exposto à LAN (firewall
> restrito à sub-rede local). **Nunca** exponha essas portas direto na internet.
