#!/bin/sh
docker compose -f docker-compose.dev.yml up --build -d

echo "To start backend development server, execute 'flask run --debug' inside backend container." 