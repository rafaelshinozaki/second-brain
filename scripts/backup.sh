#!/usr/bin/env bash
# Backup of the Second Brain: portable Neo4j dump + config.
# Neo4j Community has no reliable hot backup, so we stop Neo4j for a few seconds,
# dump offline with an ephemeral container, and start it again.
# Backups go to ./backups with 14-day retention. Schedule it with cron if you like.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$DIR/backups"
FECHA="$(date +%F_%H%M)"
RETENTION_DAYS=14
mkdir -p "$DEST"
cd "$DIR" || exit 1

echo "== Second Brain backup $FECHA =="

# 1) Stop only Neo4j.
docker compose stop neo4j >/dev/null 2>&1

# 2) Offline dump. We bypass the image entrypoint (which drops to the neo4j uid
#    and then can't write the backup dir) and run as root instead.
rm -f "$DEST/neo4j.dump"
if docker run --rm --user 0:0 --entrypoint neo4j-admin \
     -v "$DIR/data/neo4j/data:/data" \
     -v "$DEST:/backups" \
     neo4j:5.26.0 \
     database dump neo4j --to-path=/backups >/dev/null 2>&1 \
     && [ -f "$DEST/neo4j.dump" ]; then
  mv "$DEST/neo4j.dump" "$DEST/neo4j-${FECHA}.dump"
  echo "OK  Neo4j graph -> $(du -h "$DEST/neo4j-${FECHA}.dump" | cut -f1)"
else
  echo "FAILED to dump Neo4j" >&2
fi

# 3) Start Neo4j again.
docker compose start neo4j >/dev/null 2>&1
echo "OK  Neo4j restarted"

# 4) Config (compose + config + .env, which holds the Neo4j password).
tar czf "$DEST/config-${FECHA}.tgz" -C "$DIR" \
    docker-compose.yml config/config.yaml .env 2>/dev/null \
    && echo "OK  config -> config-${FECHA}.tgz"

# 5) Retention
find "$DEST" -type f \( -name '*.dump' -o -name '*.tgz' \) -mtime +"$RETENTION_DAYS" -delete 2>/dev/null
echo "== Done (retention: $RETENTION_DAYS days, dir: $DEST) =="
