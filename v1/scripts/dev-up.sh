#!/bin/sh
./scripts/dev-compose up -d --build

echo "To start backend development server, execute 'flask run --debug' inside backend container." 