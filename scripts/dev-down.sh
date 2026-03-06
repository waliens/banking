#!/bin/bash
set -euo pipefail

# Stop the v2 development environment and remove volumes.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
V2_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

docker compose -f "$V2_DIR/docker-compose.dev.yml" down -v
