"""ML prediction with subprocess isolation for memory safety."""

import logging
import multiprocessing
import os
from typing import Any

import numpy as np
from joblib import load

from app.config import settings
from app.ml.feature_extractor import CategoryEncoder
from app.models.ml_model import MLModel

logger = logging.getLogger(__name__)


class NoValidModelError(Exception):
    pass


class InferenceError(Exception):
    pass


def _run_inference(
    model_filepath: str,
    class_level: str,
    db_url: str,
    transactions_data: list[dict[str, Any]],
    result_queue: "multiprocessing.Queue[Any]",
) -> None:
    """Run inference in a subprocess to avoid memory leaks."""
    try:
        import datetime
        from decimal import Decimal
        from types import SimpleNamespace

        # Reconstruct lightweight transaction objects for the pipeline
        tx_objects = []
        for td in transactions_data:
            tx = SimpleNamespace(
                id=td["id"],
                description=td["description"],
                date=datetime.date.fromisoformat(td["date"]),
                amount=Decimal(td["amount"]),
                id_source=td["id_source"],
                id_dest=td["id_dest"],
            )
            tx_objects.append(tx)

        pipeline = load(model_filepath)
        y_proba = pipeline.predict_proba(tx_objects)
        y_pred = pipeline.steps[1][1].classes_[np.argmax(y_proba, axis=1)]

        # Decode category IDs using a fresh DB session
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.database import Base

        sub_engine = create_engine(db_url, pool_pre_ping=True)
        SubSession = sessionmaker(bind=sub_engine, autoflush=False, expire_on_commit=False)
        sub_db = SubSession()
        try:
            encoder = CategoryEncoder(sub_db, level=class_level)
            category_ids = encoder.inverse_transform(y_pred)
        finally:
            sub_db.close()
            sub_engine.dispose()

        probas = np.max(y_proba, axis=1).tolist()
        result_queue.put((category_ids.tolist(), probas))
    except Exception as e:
        result_queue.put(e)


def predict_categories(
    db: "Any",
    transactions: list[Any],
) -> list[tuple[int | None, float]]:
    """Predict categories for a list of transactions.

    Returns list of (category_id, probability) tuples.
    Raises NoValidModelError if no valid model exists.
    """
    if not transactions:
        return []

    valid_model = db.query(MLModel).filter(MLModel.state == "valid").order_by(MLModel.id.desc()).first()
    if valid_model is None:
        raise NoValidModelError("No valid model available for prediction")

    model_filepath = os.path.join(settings.model_path, valid_model.filename)
    metadata = valid_model.metadata_ or {}
    class_level = metadata.get("class_level", "fine")

    # Serialize transactions for subprocess
    transactions_data = [
        {
            "id": t.id,
            "description": t.description,
            "date": t.date.isoformat(),
            "amount": str(t.amount),
            "id_source": t.id_source,
            "id_dest": t.id_dest,
        }
        for t in transactions
    ]

    result_queue: multiprocessing.Queue[Any] = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_run_inference,
        args=(model_filepath, class_level, str(settings.database_url), transactions_data, result_queue),
    )
    try:
        process.start()
        process.join(timeout=300)
    finally:
        if process.is_alive():
            process.terminate()

    if result_queue.empty():
        raise InferenceError("Inference process did not produce results")

    result = result_queue.get()
    result_queue.close()

    if isinstance(result, Exception):
        raise InferenceError("Inference process failed") from result

    category_ids, probas = result
    return list(zip(category_ids, probas))


def predict_category(
    db: "Any",
    transaction: Any,
) -> tuple[int | None, float]:
    """Predict category for a single transaction."""
    results = predict_categories(db, [transaction])
    if not results:
        return None, 0.0
    return results[0]
