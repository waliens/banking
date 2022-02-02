import os 
import logging

import numpy as np
from joblib import dump
from scipy.sparse import data
from scipy.sparse.construct import rand
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, make_scorer

from sqlalchemy.sql.expression import update

from db.models import MLModelFile, MLModelState, Transaction
from .feature_extractor import belfius_transformer, CategoryEncoder


class ModelBeingTrainedException(Exception):
  pass


def get_max_samples_leaf(n_samples):
  values = list({int(v * n_samples) for v in [0.00005, 0.0001, 0.0025, 0.005, 0.01]})
  values.extend([1])
  return list({v for v in values if v > 0})


def train_model(session, data_source="belfius", required_sample_size=50, random_state=42, class_level="fine"):
  if data_source not in {'belfius'}:
    raise ValueError("not supported for other data then beflius")

  transformer = belfius_transformer()
  transactions = Transaction.query.filter(Transaction.data_source == data_source).all()
  labeled_idxs = np.array([i for i, t in enumerate(transactions) if t.id_category is not None])

  n_samples = labeled_idxs.shape[0]

  if MLModelFile.has_models_in_state(MLModelState.TRAINING, target=data_source):
    raise ModelBeingTrainedException("model being trained for target")
  if n_samples < required_sample_size:
    return

  # save model in training mode
  model_filename = MLModelFile.generate_filename()
  model_file = MLModelFile(filename=model_filename, target=data_source, metadata_={"class_level": class_level}, state=MLModelState.TRAINING)
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
    estimator = ExtraTreesClassifier(n_estimators=500, random_state=random_state)
    
    n_features = features.shape[1]
    param_grid = { 'min_samples_leaf': get_max_samples_leaf(n_samples), 'max_features': [int(np.sqrt(n_features)), n_features// 2, n_features] }
    kfold = KFold(n_splits=5, shuffle=True, random_state=random_state)
    gsearch = GridSearchCV(estimator, param_grid, scoring=make_scorer(accuracy_score), refit=True, cv=kfold)
    gsearch.fit(x, y)
    
    logging.getLogger(__name__).info("finish tuning model '{}' for target '{}' (cv_score={}, best_params={})".format(
      model_file.filename, model_file.target, gsearch.best_score_, gsearch.best_params_))

    pipeline = Pipeline([
      ('features', transformer), 
      ('model', gsearch.best_estimator_)
    ])
    
    model_path = os.getenv('MODEL_PATH')
    model_filepath = os.path.join(model_path, model_file.filename)
    os.makedirs(model_path, exist_ok=True)
    logging.getLogger(__name__).info("dump trained model model into '{}'")

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
