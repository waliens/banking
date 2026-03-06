"""ML model training for transaction categorization."""

import hashlib
import logging
import math
import os

import numpy as np
from joblib import dump
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, make_scorer
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.pipeline import Pipeline
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.config import settings
from app.ml.feature_extractor import CategoryEncoder, bank_csv_transformer
from app.models.category import Category
from app.models.ml_model import MLModel
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class ModelBeingTrainedError(Exception):
    pass


class NotEnoughDataError(Exception):
    pass


def category_fingerprint(db: Session) -> str:
    """Hash of all category IDs + parent relationships. Changes when tree is modified."""
    categories = db.query(Category).order_by(Category.id).all()
    parts = [f"{c.id}:{c.id_parent}" for c in categories]
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def _get_min_samples_leaf(n_samples: int) -> list[int]:
    min_leaf = max(1, int(math.log2(n_samples)))
    return [min_leaf, 2 * min_leaf, 5 * min_leaf, 10 * min_leaf]


def train_model(
    db: Session,
    min_samples: int = 50,
    random_state: int = 42,
    class_level: str = "fine",
) -> MLModel:
    """Train a new ML model for transaction categorization.

    Raises ModelBeingTrainedError if a model is already training.
    Raises NotEnoughDataError if fewer than min_samples labeled transactions exist.
    """
    # Check no model already training
    training = db.query(MLModel).filter(MLModel.state == "training").first()
    if training is not None:
        raise ModelBeingTrainedError("A model is already being trained")

    # Fetch labeled transactions (those with at least one category split)
    transactions = db.query(Transaction).filter(Transaction.category_splits.any()).all()
    n_samples_actual = len(transactions)

    if n_samples_actual < min_samples:
        raise NotEnoughDataError(f"Need at least {min_samples} labeled transactions, got {n_samples_actual}")

    # Create model record in training state
    model_filename = MLModel.generate_filename()
    model_record = MLModel(filename=model_filename, metadata_={"class_level": class_level}, state="training")
    db.add(model_record)
    db.commit()
    db.refresh(model_record)

    try:
        transformer = bank_csv_transformer()
        transformer.fit(transactions)
        features = transformer.transform(transactions)

        category_ids = np.array([t.category_splits[0].id_category for t in transactions])
        encoder = CategoryEncoder(db, level=class_level)
        y = encoder.transform(category_ids)

        n_features = features.shape[1]
        estimator = ExtraTreesClassifier(n_estimators=500, random_state=random_state, n_jobs=1)
        param_grid = {
            "min_samples_leaf": _get_min_samples_leaf(n_samples_actual),
            "max_features": [int(np.sqrt(n_features)), n_features // 2, n_features],
        }
        kfold = KFold(n_splits=5, shuffle=True, random_state=random_state)
        gsearch = GridSearchCV(
            estimator, param_grid, scoring=make_scorer(accuracy_score), refit=True, cv=kfold, n_jobs=1
        )
        gsearch.fit(features, y)

        logger.info(
            "Finished tuning model '%s' (cv_score=%s, best_params=%s)",
            model_record.filename,
            gsearch.best_score_,
            gsearch.best_params_,
        )

        pipeline = Pipeline([("features", transformer), ("model", gsearch.best_estimator_)])

        model_dir = settings.model_path
        os.makedirs(model_dir, exist_ok=True)
        model_filepath = os.path.join(model_dir, model_record.filename)

        db.refresh(model_record)
        if model_record.state == "training":
            dump(pipeline, model_filepath)
            model_record.state = "valid"
            model_record.metadata_ = {
                "params": gsearch.best_params_,
                "cv_score": gsearch.best_score_,
                "n_samples": n_samples_actual,
                "category_fingerprint": category_fingerprint(db),
                **(model_record.metadata_ or {}),
            }
            db.commit()
            db.refresh(model_record)

    except Exception:
        model_record.state = "invalid"
        db.commit()
        raise

    return model_record


def should_train(db: Session, min_samples: int = 50) -> bool:
    """Check if training is warranted: enough data and something changed since last valid model."""
    n_labeled = db.query(Transaction).filter(Transaction.category_splits.any()).count()
    if n_labeled < min_samples:
        return False

    # Check if a model is already training
    if db.query(MLModel).filter(MLModel.state == "training").first() is not None:
        return False

    last_valid = db.query(MLModel).filter(MLModel.state == "valid").order_by(MLModel.id.desc()).first()
    if last_valid is None:
        return True

    metadata = last_valid.metadata_ or {}
    old_n_samples = metadata.get("n_samples", 0)
    old_fingerprint = metadata.get("category_fingerprint", "")

    if n_labeled != old_n_samples:
        return True
    if category_fingerprint(db) != old_fingerprint:
        return True

    return False


def invalidate_all_models(db: Session) -> None:
    """Set all non-deleted models to invalid."""
    db.execute(update(MLModel).where(MLModel.state != "deleted").values(state="invalid"))
    db.commit()


def delete_invalid_models(db: Session) -> None:
    """Delete .pkl files for invalid models and set their state to deleted."""
    invalid_models = db.query(MLModel).filter(MLModel.state == "invalid").all()
    for m in invalid_models:
        filepath = os.path.join(settings.model_path, m.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        m.state = "deleted"
    if invalid_models:
        db.commit()
