# Banking app

Requires docker. To launch the production server (from repository root): `docker-compose -f docker-compose.yml build && docker-compose -f docker-compose.yml up`

Services:
- Client (frontend) served on `localhost:8080`
- Server (api) served on `localhost:5000`
- Redis server: `localhost:6379`
- Postgres database: `localhost:5432`
- Celery worker (not served, interaction through redis)

Data:
- machine learning model files stored in docker `models_volume` volume
- postgres database stored in docker `db_volume_pg` volume

Any change in database schema should be handled automatically when launching the production app.    

# Devlopment env

We provide a docker compose file for development. This allows code modifications to directly be taken into account and repercuted on the running application without the need for relaunching the whole architecture.

```docker-compose -f docker-compose.dev.yml build && docker-compose -f docker-compose.dev.yml up```

For generating database migrations on schema change (with alembic), use `docker-compose.db-revision.yml`.

# Future features

- automated integration of data from Splitwise/Tricount to correct repayment values
- automated integration of investments data (pension savings, stocks, crypto)
- tabular yearly report for expenses

# Security disclaimer
This app is authentication-free and stores sensitive banking transactions history information. This is inherently insecure so please only deploy this application if you know what you are doing.