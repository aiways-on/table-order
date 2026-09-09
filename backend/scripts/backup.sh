#!/usr/bin/env sh
# Scheduled pg_dump backup with retention. [RES-12][NFR-R4]
# Intended to run in the `backup` compose service on a schedule.
set -e

: "${POSTGRES_USER:?POSTGRES_USER required}"
: "${POSTGRES_DB:?POSTGRES_DB required}"
: "${PGHOST:=db}"
: "${BACKUP_DIR:=/backups}"
: "${BACKUP_RETENTION_DAYS:=7}"

mkdir -p "$BACKUP_DIR"
TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$BACKUP_DIR/tableorder_${TS}.sql.gz"

echo "[backup] dumping $POSTGRES_DB -> $OUT"
pg_dump -h "$PGHOST" -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT"

echo "[backup] pruning backups older than ${BACKUP_RETENTION_DAYS} days"
find "$BACKUP_DIR" -name 'tableorder_*.sql.gz' -mtime +"$BACKUP_RETENTION_DAYS" -delete

echo "[backup] done"
# Restore (documented): gunzip -c <file>.sql.gz | psql -h <host> -U <user> <db>
