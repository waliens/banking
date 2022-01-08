from db.database import init_db
from db.models import Category, Transaction
from ml.feature_extractor import CategoryEncoder, belfius_transformer
import os

if __name__ == "__main__":
  Session, engine = init_db()
  session = Session()
  transactions = Transaction.query.all()
  transformer = belfius_transformer()
  transformer.fit(transactions)
  features = transformer.transform(transactions)
  print(features.shape)

  encoderf = CategoryEncoder(level='fine')
  encoderc = CategoryEncoder(level='coarse')
