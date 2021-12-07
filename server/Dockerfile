FROM python:3.9.9-slim-bullseye

RUN pip install python-dotenv
RUN pip install sqlalchemy sqlalchemy-utils
RUN pip install flask flask-cors


WORKDIR /app

ADD db ./db
ADD parsing ./parsing
ADD banking.py ./banking.py

EXPOSE 5000

ENTRYPOINT ["flask", "run"]