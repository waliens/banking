import math
import multiprocessing
import os
import logging
from typing import Optional, Set

import numpy as np
from joblib import dump
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, make_scorer

from sqlalchemy import select
from sqlalchemy.sql.expression import update

from db.models import MLModelFile, MLModelState, Transaction
from .feature_extractor import bank_csv_transformer, CategoryEncoder


class ModelBeingTrainedException(Exception):
  pass


class NotEnoughDataToTrain(Exception):
  pass


LOGGER = logging.getLogger("model_train")


def get_min_samples_leaf(n_samples):
  # This prevents the model to grow too big when
  # the dataset grows reducing memory footpring
  # and loading time
  min_leaf_size = max(1, int(math.log2(n_samples)))

  # Generate values directly from min_leaf_size
  return [
    min_leaf_size,
    2 * min_leaf_size,
    5 * min_leaf_size,
    10 * min_leaf_size
  ]


def train_model(session, required_sample_size: int=50, random_state: int=42, class_level="fine"):
  transformer = bank_csv_transformer()
  query_results = session.execute(
    select(Transaction).where(
      Transaction.id_category != None
    )
  ).unique().all()
  transactions = [r[0] for r in query_results]
  labeled_idxs = np.arange(len(transactions))

  n_samples = labeled_idxs.shape[0]

  if MLModelFile.has_models_in_state(MLModelState.TRAINING):
    raise ModelBeingTrainedException("model being trained")
  if n_samples < required_sample_size:
    raise NotEnoughDataToTrain(f"not enough data to train, only got {n_samples} samples, but requires {required_sample_size}")

  # save model in training mode
  model_filename = MLModelFile.generate_filename()
  model_file = MLModelFile(filename=model_filename, metadata_={"class_level": class_level}, state=MLModelState.TRAINING)
  session.add(model_file)
  session.commit()

  try:
    transformer.fit(transactions)
    features = transformer.transform(transactions)

    x = features[labeled_idxs]
    categories = np.array([transactions[idx].id_category for idx in labeled_idxs])
    encoder = CategoryEncoder(level=class_level)
    y = encoder.transform(categories)

    # create model
    estimator = ExtraTreesClassifier(n_estimators=500, random_state=random_state, n_jobs=1)

    n_features = features.shape[1]
    param_grid = { 'min_samples_leaf': get_min_samples_leaf(n_samples), 'max_features': [int(np.sqrt(n_features)), n_features// 2, n_features] }
    kfold = KFold(n_splits=5, shuffle=True, random_state=random_state)
    gsearch = GridSearchCV(estimator, param_grid, scoring=make_scorer(accuracy_score), refit=True, cv=kfold, n_jobs=1)
    gsearch.fit(x, y)

    LOGGER.info(f"finish tuning model '{model_file.filename}' (cv_score={gsearch.best_score_}, best_params={gsearch.best_params_})")

    pipeline = Pipeline([
      ('features', transformer),
      ('model', gsearch.best_estimator_)
    ])

    model_path = os.getenv('MODEL_PATH')
    model_filepath = os.path.join(model_path, model_file.filename)
    os.makedirs(model_path, exist_ok=True)
    LOGGER.info(f"dump trained model model into '{model_path}'")

    # check if TRAINING state hasn't change
    session.refresh(model_file)
    if model_file.state == MLModelState.TRAINING:
      dump(pipeline, model_filepath)
      model_file.state = MLModelState.VALID
      model_file.metadata_ = {
        'params': gsearch.best_params_,
        'cv_score': gsearch.best_score_,
        **model_file.metadata_
      }
      session.add(model_file)
      session.commit()

  except Exception as e:
    model_file.state = MLModelState.INVALID
    session.commit()
    raise e


def invalidate_all_models(session):
  session.execute(update(MLModelFile).where(Transaction.state==MLModelState.VALID).values(state=MLModelState.INVALID))
  session.commit()
