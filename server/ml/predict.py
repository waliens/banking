import os
import numpy as np

from joblib import load
from sqlalchemy import Integer
from sqlalchemy.sql.expression import and_

from db.models import MLModelState, MLModelFile, Category

from .feature_extractor import CategoryEncoder


class TooManyAvailableModelsException(Exception):
  pass


class NoValidModelException(Exception):
  pass


def predict_for_source(transactions, source, raise_if_no_model=False):
  valid_models = MLModelFile.get_models_by_state(MLModelState.VALID, target=source)
  if len(valid_models) > 1:
    raise TooManyAvailableModelsException("several valid models to choose from")
  elif len(valid_models) == 0:
    if raise_if_no_model:
      raise NoValidModelException("no model that satisfies the conditions")
    else:
      return [None] * len(transactions), [0] * len(transactions)

  model_file = valid_models[0]
  model_filepath = os.path.join(os.getenv('MODEL_PATH'), model_file.filename)
  pipeline = load(model_filepath)
  
  y_proba = pipeline.predict_proba(transactions)
  y_pred = pipeline.steps[1][1].classes_[np.argmax(y_proba, axis=1)]
  encoder = CategoryEncoder(level=model_file.metadata_['class_level'])  
  ids = encoder.inverse_transform(y_pred)
  category_map = {c.id: c for c in Category.query.all()}
  return [category_map[id_] for id_ in ids], np.max(y_proba, axis=1).tolist()


def predict_category(transaction):
  categories, probas = predict_for_source([transaction], transaction.data_source, raise_if_no_model=True)
  return categories[0], probas[0]


def predict_categories(transactions):
  """Predict categories and probas for an iterable of transactions"""
  sources = {t.data_source for t in transactions}
  out_list = [(None, 0)] * len(transactions)
  for data_source in sources:
    indexes, transacs_from_source = zip(*filter(lambda t: (t[1].data_source == data_source), enumerate(transactions)))
    categories, probas = predict_for_source(transacs_from_source, data_source)
    for i, c, p in zip(indexes, categories, probas):
      out_list[i] = (c, p)
  if len(out_list) == 0:
    return [], [] 
  return zip(*out_list)
