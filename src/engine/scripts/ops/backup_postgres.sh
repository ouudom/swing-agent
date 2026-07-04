#!/usr/bin/env sh
set -eu

# Nightly Postgres backup. Keep last 7 compressed dumps.
# Usage from swing-agent/src:
#   ./scripts/backup_postgres.sh

BACKUP_DIR="${BACKUP_DIR:-./backups/postgres}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-swing_agent}"
POSTGRES_USER="${POSTGRES_USER:-swing_agent}"

mkdir -p "$BACKUP_DIR"

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="$BACKUP_DIR/${POSTGRES_DB}_${stamp}.sql.gz"

PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}" \
  pg_dump \
    --host "$POSTGRES_HOST" \
    --port "$POSTGRES_PORT" \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --no-owner \
    --no-privileges \
  | gzip -9 > "$out"

find "$BACKUP_DIR" -name "${POSTGRES_DB}_*.sql.gz" -type f \
  | sort -r \
  | awk 'NR>7' \
  | xargs -r rm -f

echo "$out"
