#!/bin/sh
echo "Run current migrations..."
./scripts/dev-launch-env.sh
echo "Generate differential migration..."
docker compose -f docker-compose.dev.yml --profile migration up --build -d
sleep 3
docker compose -f docker-compose.dev.yml --profile migration logs server-db-revision > /dev/stdout 2>&1
# echo "Shutdown migration generation container..."
docker compose -f docker-compose.dev.yml --profile migration stop server-db-revision
docker compose -f docker-compose.dev.yml --profile migration rm -f server-db-revision

echo "Chowning the migration files to the current user..."
sudo chown $(id -u):$(id -g) ./server/alembic/versions/ -R