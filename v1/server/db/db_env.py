import os

def get_db_url():
  username = os.getenv("DB_USER")
  password = os.getenv("DB_PASSWORD")
  host = os.getenv("DB_HOST")
  dbname = os.getenv("DB_NAME")
  return "postgresql+psycopg2://{}:{}@{}/{}".format(username, password, host, dbname)
