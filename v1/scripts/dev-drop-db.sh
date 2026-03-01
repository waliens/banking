#!/bin/sh
docker compose -f docker-compose.dev.yml down celery_worker database -v
docker compose -f docker-compose.dev.yml up celery_worker database 