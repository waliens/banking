#!/bin/bash
set -euo pipefail

# Start the v2 development environment.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
V2_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

docker compose -f "$V2_DIR/docker-compose.dev.yml" up -d --build

echo "Development environment started."
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  Database: localhost:5433"
