#!/bin/bash

# Default values
PROD_IP=${PROD_IP:-$1}
CONTAINER_NAME=${CONTAINER_NAME:-banking-database-1}
DB_NAME=${DB_NAME:-banking}
DB_USER=${DB_USER:-admin}
BACKUP_DIR=${BACKUP_DIR:-./backups}
TMP_REMOTE_FILE="~/db_backup.sql"

# Ensure backup directory exists and is writable
mkdir -p $BACKUP_DIR
chmod +w $BACKUP_DIR

# Generate backup filename
BACKUP_FILE="${DB_NAME}_$(date +'%Y%m%d_%H%M%S').sql"

# SSH into the remote server and run pg_dump inside the container
echo "Running backup on remote server..."
ssh -T -o "ControlMaster=no" rmormont@$PROD_IP << EOF
  docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $TMP_REMOTE_FILE
  chmod 744 $TMP_REMOTE_FILE
EOF

# Check if the SSH command was successful
if [ $? -ne 0 ]; then
  echo "Error: SSH command failed."
  exit 1
fi

# Copy the backup file from the remote server to the local machine using rsync
echo "Copying backup to local machine..."
rsync -avz rmormont@$PROD_IP:$TMP_REMOTE_FILE $BACKUP_DIR/$BACKUP_FILE

# Check if the rsync command was successful
if [ $? -ne 0 ]; then
  echo "Error: rsync command failed."
  exit 1
fi

# Clean up the backup file on the remote server
ssh -T -o "ControlMaster=no" rmormont@$PROD_IP "rm $TMP_REMOTE_FILE"

echo "Backup completed: $BACKUP_DIR/$BACKUP_FILE"