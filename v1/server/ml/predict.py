import os
import numpy as np
import multiprocessing

from joblib import load
from sqlalchemy import Integer
from sqlalchemy.sql.expression import and_

from db.models import MLModelState, MLModelFile, Category

from .feature_extractor import CategoryEncoder


class TooManyAvailableModelsException(Exception):
  pass


class NoValidModelException(Exception):
  pass


class InferenceException(Exception):
  pass


def run_inference(model_filepath, model_metadata, transactions, result_queue):
  try:
    pipeline = load(model_filepath)
    y_proba = pipeline.predict_proba(transactions)
    y_pred = pipeline.steps[1][1].classes_[np.argmax(y_proba, axis=1)]

    encoder = CategoryEncoder(level=model_metadata['class_level'])
    ids = encoder.inverse_transform(y_pred)
    category_map = {c.id: c for c in Category.query.all()}
    categories = [category_map[id_] for id_ in ids]
    probas = np.max(y_proba, axis=1).tolist()
    result_queue.put((categories, probas))
  except Exception as e:
    result_queue.put(e)


def predict_for_source(transactions, raise_if_no_model=False):
  valid_models = MLModelFile.get_models_by_state(MLModelState.VALID)
  if len(valid_models) > 1:
    raise TooManyAvailableModelsException("several valid models to choose from")
  elif len(valid_models) == 0:
    if raise_if_no_model:
      raise NoValidModelException("no model that satisfies the conditions")
    else:
      return [None] * len(transactions), [0] * len(transactions)

  model_file = valid_models[0].as_dict()
  model_filepath = os.path.join(os.getenv('MODEL_PATH'), model_file["filename"])

  # Need to load and run the model in a separate process to avoid
  # memory leaks in the main process. This adds an overhead but
  # it prevents the memory leaks so it's worth it.
  result_queue = multiprocessing.Queue()
  process = multiprocessing.Process(
    target=run_inference,
    args=(
      model_filepath,
      model_file["metadata_"],
      transactions,
      result_queue
    )
  )
  try:
    process.start()
    process.join()
  finally:
    if process.is_alive():
      process.terminate()

  result = result_queue.get()
  result_queue.close()
  result_queue.join_thread()

  if isinstance(result, Exception):
    raise InferenceException("Inference process failed") from result

  return result


def predict_category(transaction):
  categories, probas = predict_for_source([transaction], raise_if_no_model=True)
  return categories[0], probas[0]


def predict_categories(transactions):
  """Predict categories and probas for an iterable of transactions"""
  if not transactions or len(transactions) == 0:
    return [], []
  return predict_for_source(transactions, raise_if_no_model=True)
