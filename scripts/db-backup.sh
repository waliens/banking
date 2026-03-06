#!/bin/bash
set -euo pipefail

# Back up the production v2 database from a remote server.
#
# Usage: ./scripts/db-backup.sh [PROD_IP]
# Example: ./scripts/db-backup.sh 192.168.1.100

PROD_IP="${PROD_IP:-${1:-}}"
CONTAINER_NAME="${CONTAINER_NAME:-v2-db-1}"
DB_NAME="${DB_NAME:-banking_v2}"
DB_USER="${DB_USER:-banking}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TMP_REMOTE_FILE="~/db_backup_v2.sql"

if [ -z "$PROD_IP" ]; then
  echo "Usage: $0 <PROD_IP>"
  echo "  or set PROD_IP environment variable"
  exit 1
fi

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="${DB_NAME}_$(date +'%Y%m%d_%H%M%S').sql"

echo "Running backup on remote server ($PROD_IP)..."
ssh -T -o "ControlMaster=no" rmormont@"$PROD_IP" << EOF
  docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $TMP_REMOTE_FILE
  chmod 644 $TMP_REMOTE_FILE
EOF

echo "Copying backup to local machine..."
rsync -avz rmormont@"$PROD_IP":"$TMP_REMOTE_FILE" "$BACKUP_DIR/$BACKUP_FILE"

ssh -T -o "ControlMaster=no" rmormont@"$PROD_IP" "rm $TMP_REMOTE_FILE"

echo "Backup completed: $BACKUP_DIR/$BACKUP_FILE"
