#!/usr/bin/env bash
# One-shot setup for the AI Second Brain (native Ollama path).
#   - checks Docker & Ollama
#   - pulls the local models and builds qwen2.5-brain (bigger context window)
#   - creates .env with a random Neo4j password
#   - starts the stack
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

say "Checking prerequisites"
command -v docker >/dev/null || die "Docker is not installed. See https://docs.docker.com/get-docker/"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required (docker compose)."
if ! command -v ollama >/dev/null; then
  cat <<'MSG'
Ollama is not installed on the host.
  - Install it from https://ollama.com  (recommended: fastest, uses your GPU), OR
  - run Ollama in Docker with the overlay:
      docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d
    and pull the models inside the container (see docker-compose.ollama.yml).
Then re-run this script (it will skip the model pull if you used the overlay).
MSG
  die "Ollama not found."
fi

say "Pulling local models (this can take a while the first time)"
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct

say "Building qwen2.5-brain (qwen2.5:7b-instruct with a larger context window)"
printf 'FROM qwen2.5:7b-instruct\nPARAMETER num_ctx 8192\n' > "$DIR/Modelfile.brain"
ollama create qwen2.5-brain -f "$DIR/Modelfile.brain"
rm -f "$DIR/Modelfile.brain"

if [ ! -f .env ]; then
  say "Creating .env with a random Neo4j password"
  PASS="$(openssl rand -base64 24 | tr -d '/+=' | head -c 28)"
  sed "s|change_me_please|$PASS|" .env.example > .env
  chmod 600 .env
else
  say ".env already exists — keeping it"
fi

# Linux note: host.docker.internal needs Ollama listening on all interfaces.
if [ "$(uname -s)" = "Linux" ]; then
  cat <<'MSG'

NOTE (Linux): containers reach Ollama via host.docker.internal. If the MCP logs
show connection errors to Ollama, make Ollama listen on all interfaces:
    sudo systemctl edit ollama       # add:  Environment="OLLAMA_HOST=0.0.0.0"
    sudo systemctl restart ollama
(Or use the containerized Ollama overlay — see docker-compose.ollama.yml.)
MSG
fi

say "Building the MCP image and starting the stack (first build ~1 min)"
mkdir -p data/neo4j/data data/neo4j/logs
docker compose up -d --build

say "Done. Give Neo4j ~40s on first boot, then check:"
echo "  docker compose ps"
echo "  curl -s http://127.0.0.1:8020/health"
echo "  Neo4j Browser: http://127.0.0.1:7474  (user: neo4j, password: see .env)"
echo "  MCP endpoint for agents: http://127.0.0.1:8020/mcp"
