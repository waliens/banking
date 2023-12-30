FROM python:3.10-slim-bullseye AS backend

RUN pip install python-dotenv \
    sqlalchemy sqlalchemy-utils \
    flask flask-cors \
    celery redis \
    scikit-learn nltk \
    pdfminer beautifulsoup4 \
    alembic psycopg2-binary \
    Flask-JWT-Extended \
    python-dateutil

WORKDIR /app

ADD ml ./ml
ADD db ./db
ADD parsing ./parsing
ADD impl ./impl
ADD background ./background
ADD alembic ./alembic
ADD banking.py ./banking.py
ADD alembic.ini ./alembic.ini

ENV FLASK_APP=banking
ENV FLASK_RUN_HOST=0.0.0.0
ENV MODEL_PATH=/models
ENV FLASK_ENV=production

FROM backend as task-runner
RUN echo "building task-runner stage"
CMD ["celery", "-A", "banking.celery", "worker"]

FROM backend AS server 
RUN echo "building server stage"
CMD ["flask", "run"]
