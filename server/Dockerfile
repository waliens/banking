FROM python:3.9.9-slim-bullseye

RUN pip install python-dotenv
RUN pip install sqlalchemy sqlalchemy-utils
RUN pip install flask flask-cors
RUN pip install celery redis
RUN pip install scikit-learn nltk
RUN pip install pdfminer beautifulsoup4
RUN pip install alembic psycopg2-binary
RUN pip install Flask-JWT-Extended

WORKDIR /app

ADD ml ./ml
ADD db ./db
ADD parsing ./parsing
ADD impl ./impl
ADD background ./background
ADD alembic ./alembic
ADD banking.py ./banking.py
ADD alembic.ini ./alembic.ini

EXPOSE 5000
