# Banking app

Requires docker. To launch the production server (from repository root): `docker-compose -f docker-compose.yml build && docker-compose -f docker-compose.yml up`

Services:
- Client (frontend) served on `localhost:8080`
- Server (api) served on `localhost:5000`
- Redis server: `localhost:6379`
- Celery worker (not served, interaction through redis)

Data:
- machine learning model files stored in docker `models_volume` volume
- sqlite database stored in docker `db_volume` volume


# Future features

- automated integration of data from Splitwise/Tricount to correct repayment values
- automated integration of investments data (pension savings, stocks, crypto)
- more reports (montly report per category)