#!/bin/bash
set -euo pipefail

# Deploy script: pull latest images and restart services on the production server.
#
# Usage: ./scripts/deploy.sh [PROD_IP]
# Example: ./scripts/deploy.sh 192.168.1.100
#
# Expects the v2/ directory (with docker-compose.yml and .env) to be present
# on the remote server at ~/banking/v2/

PROD_IP="${PROD_IP:-${1:-}}"
REMOTE_DIR="${REMOTE_DIR:-~/banking/v2}"

if [ -z "$PROD_IP" ]; then
  echo "Usage: $0 <PROD_IP>"
  echo "  or set PROD_IP environment variable"
  exit 1
fi

echo "Deploying to $PROD_IP..."

ssh -T rmormont@"$PROD_IP" << EOF
  set -e
  cd $REMOTE_DIR
  echo "Pulling latest images..."
  docker compose pull backend frontend
  echo "Restarting services..."
  docker compose up -d --no-build
  echo "Cleaning up old images..."
  docker image prune -f
EOF

echo "Deploy complete!"
