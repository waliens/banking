FROM python:3.9.9-slim-bullseye

RUN pip install python-dotenv
RUN pip install sqlalchemy sqlalchemy-utils
RUN pip install flask 

WORKDIR /app

ADD db /app/db
ADD parsing /app/parsing
ADD banking.py /app/banking.py

EXPOSE 5000

ENTRYPOINT ["flask", "run"]