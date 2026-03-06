#!/bin/bash
set -euo pipefail

# Restore a database backup into the v2 dev environment.
#
# Usage: ./scripts/db-restore.sh [BACKUP_FILE]
# If no file is provided, uses the latest .sql file in ./backups/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
V2_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKUP_DIR="${BACKUP_DIR:-$V2_DIR/backups}"
DB_SERVICE_NAME="${DB_SERVICE_NAME:-db}"
DB_NAME="${DB_NAME:-banking_v2}"
DB_USER="${DB_USER:-banking}"

COMPOSE="docker compose -f $V2_DIR/docker-compose.dev.yml"

get_latest_backup() {
  ls -t "$BACKUP_DIR"/*.sql 2>/dev/null | head -1
}

BACKUP_FILE="${1:-$(get_latest_backup)}"

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file not found: ${BACKUP_FILE:-<none>}"
  echo "Usage: $0 [BACKUP_FILE]"
  exit 1
fi

# Check if database container is running
if ! $COMPOSE ps --status running | grep -q "$DB_SERVICE_NAME"; then
  echo "Error: Database container is not running. Start with: ./scripts/dev-up.sh"
  exit 1
fi

read -p "This will drop the existing database. The backend should be stopped. Continue? (y/n): " confirm
if [ "$confirm" != "y" ]; then
  echo "Aborted."
  exit 1
fi

echo "Dropping existing database..."
$COMPOSE exec "$DB_SERVICE_NAME" dropdb -f --if-exists -U "$DB_USER" "$DB_NAME"
$COMPOSE exec "$DB_SERVICE_NAME" createdb -U "$DB_USER" -O "$DB_USER" "$DB_NAME"

echo "Restoring from $BACKUP_FILE..."
cat "$BACKUP_FILE" | $COMPOSE exec -T "$DB_SERVICE_NAME" psql -U "$DB_USER" -d "$DB_NAME"

echo "Database restored from: $BACKUP_FILE"
