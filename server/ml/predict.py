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


def predict_category(transaction):
  valid_models = MLModelFile.get_models_by_state(MLModelState.VALID, target=transaction.data_source)
  if len(valid_models) > 1:
    raise TooManyAvailableModelsException("several valid models to choose from")
  elif len(valid_models) == 0:
    raise NoValidModelException("no model that satisfies the conditions")
  
  model_file = valid_models[0]
  model_filepath = os.path.join(os.getenv('MODEL_PATH'), model_file.filename)
  pipeline = load(model_filepath)
  
  y_proba = pipeline.predict_proba([transaction])
  y_pred = np.argmax(y_proba, axis=1)
  encoder = CategoryEncoder(level=model_file.metadata_['class_level'])  
  ids = encoder.inverse_transform(y_pred)
  return Category.query.get(ids[0]), np.max(y_proba)