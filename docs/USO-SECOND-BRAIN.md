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
- **Acesso remoto habilitado:** as portas foram publicadas na LAN e o MCP levou
  um patch (`host='0.0.0.0'`) para aceitar conexões de fora. Firewall do Windows
  liberado nas portas `8020/7474/7687` **só para a sub-rede local**.
- **Backup automático:** tarefa agendada no Windows (`SecondBrainBackup`, diária
  03:15) via `scripts/backup.ps1` → dumps em `./backups` (retenção 14 dias).
- **Regras para agentes:** `AGENTS.md` (na raiz) define o protocolo
  *ler-antes / escrever-depois*. Vários repos do ecossistema têm
  `.cursor/rules/second-brain.mdc` apontando pro mesmo cérebro (grupo `aixelerator`).
- **Comando `/reuniao`:** versionado em [`.cursor/commands/reuniao.md`](../.cursor/commands/reuniao.md)
  — cola as notas do Granola e ele salva como memórias atômicas.
- **Conteúdo já no grafo:** ~43 memórias mapeando o ecossistema
  Aixelerator / Kainam / Mirador (repos, stacks, arquitetura, integrações).

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
    "second-brain": { "url": "http://192.168.15.2:8020/mcp" }
  }
}
```

Recarregue o Cursor e confira em **Settings → MCP**. O endpoint é **sem barra no
final** (`/mcp`, não `/mcp/`).

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

1. Extrair e aplicar o patch de host no MCP:
   ```powershell
   docker cp second-brain-mcp:/app/mcp/src/graphiti_mcp_server.py config/graphiti_mcp_server.py
   # adicione host='0.0.0.0' no bloco FastMCP(...) (ver git deste arquivo)
   ```
2. Confirmar `docker-compose.remote.yml` publicando em `192.168.15.2` e montando
   o arquivo com patch.
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

> 🔒 O MCP **não tem autenticação própria**. Só está exposto à LAN (firewall
> restrito à sub-rede local). **Nunca** exponha essas portas direto na internet.
