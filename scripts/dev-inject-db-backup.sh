#!/bin/bash

BACKUP_DIR=${BACKUP_DIR:-./backups}
DB_SERVICE_NAME=${DB_SERVICE_NAME:-database}
DB_NAME=${DB_NAME:-banking}
DB_USER=${DB_USER:-admin}
DB_PASSWORD=${DB_PASSWORD:-password}

# compose stud
DOCKER_CALL="docker compose -f docker-compose.dev.yml"
CELERY_SERVICE_NAME="celery_worker"

# Function to get the latest backup file
get_latest_backup() {
  ls -t $BACKUP_DIR/*.sql | head -1
}

# Get the backup file from the argument or use the latest one
BACKUP_FILE=${1:-$(get_latest_backup)}

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file not found: $BACKUP_FILE"
  exit 1
fi

# Check if database container is running
if ! $DOCKER_CALL ps | grep -q $DB_SERVICE_NAME; then
  echo "Error: Database container is not running."
  exit 1
fi

# Prompt the user to confirm the backend server is down
read -p "Ensure the backend server is down before proceeding. Is the backend server down? (y/n): " confirm
if [ "$confirm" != "y" ]; then
  echo "Please shut down the backend server and try again."
  exit 1
fi

# Drop the existing database and create a new one
echo "Dropping the existing database..."
$DOCKER_CALL exec $DB_SERVICE_NAME dropdb -f --if-exists -U $DB_USER $DB_NAME
$DOCKER_CALL exec $DB_SERVICE_NAME createdb -U $DB_USER -O $DB_USER $DB_NAME

# Inject the backup into the database
echo "Injecting the backup into the database..."
cat $BACKUP_FILE | $DOCKER_CALL exec -T -i $DB_SERVICE_NAME psql -U $DB_USER -d $DB_NAME

if [ $? -ne 0 ]; then
  echo "Error: Failed to inject the backup."
  exit 1
fi

echo "Database has been successfully replaced with the backup: $BACKUP_FILE"
