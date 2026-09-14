#!/usr/bin/env bash
# Nightly (or on-demand) logical backup of the MySQL database, via
# mysqldump, gzipped, timestamped, and (in a real deployment) uploaded to
# object storage by the caller -- this script only produces the file; it
# does not know where "off this host" is, since that's an environment-
# specific decision (see docs/runbook.md "Backups"). Restore drills use
# scripts/restore_db.sh against this exact file.
set -euo pipefail

log() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; exit 1; }

: "${DB_HOST:?set DB_HOST}"
: "${DB_PORT:=3306}"
: "${DB_USER:?set DB_USER}"
: "${DB_PASSWORD:?set DB_PASSWORD}"
: "${DB_NAME:?set DB_NAME}"
: "${BACKUP_DIR:=./backups}"

command -v mysqldump >/dev/null 2>&1 || fail "mysqldump is required"

mkdir -p "$BACKUP_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
out_file="$BACKUP_DIR/linksavvy-${DB_NAME}-${timestamp}.sql.gz"

log "Dumping ${DB_NAME}@${DB_HOST}:${DB_PORT} to ${out_file}"
MYSQL_PWD="$DB_PASSWORD" mysqldump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --user="$DB_USER" \
  --single-transaction \
  --routines \
  --triggers \
  --set-gtid-purged=OFF \
  "$DB_NAME" | gzip > "$out_file"

size=$(du -h "$out_file" | cut -f1)
log "Backup complete: ${out_file} (${size})"
