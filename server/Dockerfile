FROM python:3.9.9-slim-bullseye

# dev: docker run -e FLASK_APP=banking -e FLASK_ENV=development -e DB_FILE=/data/db.db -e FLASK_RUN_HOST=0.0.0.0 -v ~/data/banking/:/data -v ~/repos/banking/server/:/app/ -p 5000:5000 --rm -it bankingserv
RUN pip install python-dotenv
RUN pip install sqlalchemy sqlalchemy-utils
RUN pip install flask flask-cors
RUN pip install celery redis
RUN pip install scikit-learn nltk

WORKDIR /app

ADD db ./db
ADD parsing ./parsing
ADD impl ./impl
ADD background ./background
ADD banking.py ./banking.py

EXPOSE 5000
