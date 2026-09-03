#!/usr/bin/env bash
# Restore the Second Brain from a Neo4j dump.
# Usage:  bash scripts/restore.sh ./backups/neo4j-2026-01-01_0300.dump
# WARNING: overwrites the current 'neo4j' database.
#
# Staging is done under ./backups (NOT /tmp): some Docker setups run the daemon
# with PrivateTmp, which makes /tmp bind mounts appear empty inside containers.
set -uo pipefail
DUMP="${1:-}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$DIR/backups"
cd "$DIR"

if [ -z "$DUMP" ] || [ ! -f "$DUMP" ]; then
  echo "Usage: bash scripts/restore.sh <path-to-dump>" >&2
  echo "Available dumps:" >&2
  ls -1 "$DEST/"*.dump 2>/dev/null >&2 || echo "  (none)" >&2
  exit 1
fi

echo "== Restoring $DUMP =="
read -r -p "This OVERWRITES the current database. Continue? (type 'yes'): " ok
[ "$ok" = "yes" ] || { echo "Cancelled."; exit 1; }

STAGE="$DEST/.restore"
cleanup() { rm -rf "$STAGE"; docker compose start neo4j >/dev/null 2>&1; }
trap cleanup EXIT

docker compose stop neo4j

rm -rf "$STAGE"; mkdir -p "$STAGE"; chmod 755 "$STAGE"
cp "$DUMP" "$STAGE/neo4j.dump"; chmod 644 "$STAGE/neo4j.dump"

# Load as the neo4j uid (owner of /data), bypassing the entrypoint so restored
# files end up with the right owner.
docker run --rm --user 7474:7474 --entrypoint neo4j-admin \
  -v "$DIR/data/neo4j/data:/data" \
  -v "$STAGE:/backups" \
  neo4j:5.26.0 \
  database load neo4j --from-path=/backups --overwrite-destination=true

echo "== Restore complete. Verify in Neo4j Browser. =="
