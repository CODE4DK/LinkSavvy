#!/usr/bin/env bash
# Restores a backup produced by scripts/backup_db.sh into a target
# database. Defaults to a *new* database name (never the source's own
# name) so a restore drill can never accidentally overwrite a live
# database by a slipped environment variable -- pass DB_NAME explicitly
# to restore over an existing one (e.g. real disaster recovery), and only
# then.
set -euo pipefail

log() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; exit 1; }

: "${DB_HOST:?set DB_HOST}"
: "${DB_PORT:=3306}"
: "${DB_USER:?set DB_USER}"
: "${DB_PASSWORD:?set DB_PASSWORD}"
: "${DB_NAME:=linksavvy_restore_test}"

BACKUP_FILE="${1:?usage: restore_db.sh <path-to-backup.sql.gz>}"
[ -f "$BACKUP_FILE" ] || fail "no such file: $BACKUP_FILE"

command -v mysql >/dev/null 2>&1 || fail "mysql client is required"

start_time=$(date +%s)

log "Creating database ${DB_NAME} (if it doesn't already exist)"
MYSQL_PWD="$DB_PASSWORD" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
  -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"

log "Restoring ${BACKUP_FILE} into ${DB_NAME}@${DB_HOST}:${DB_PORT}"
gunzip -c "$BACKUP_FILE" | MYSQL_PWD="$DB_PASSWORD" mysql \
  --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" "$DB_NAME"

end_time=$(date +%s)
elapsed=$((end_time - start_time))

row_count=$(MYSQL_PWD="$DB_PASSWORD" mysql --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
  -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '${DB_NAME}';")

log "Restore complete in ${elapsed}s -- ${row_count} tables present in ${DB_NAME}"
log "Record this duration in docs/runbook.md's restore-drill log."
