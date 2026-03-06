"""Tests for ML endpoints and feature extraction."""

import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models import Account, Category, CategorySplit, Currency, MLModel, Transaction
from tests.conftest import categorize


@pytest.fixture
def ml_model_valid(db: Session) -> MLModel:
    m = MLModel(filename="test-model.pkl", state="valid", metadata_={"class_level": "fine"})
    db.add(m)
    db.flush()
    return m


class TestDescriptionPreprocessor:
    def test_removes_ref_pattern(self):
        from app.ml.feature_extractor import DescriptionPreprocessor

        pp = DescriptionPreprocessor()
        pp.fit([])
        tx = SimpleNamespace(description="Payment REF. : ABC123DEF456 at store")
        result = pp.transform([tx])
        assert "REF." not in result[0]
        assert "ABC123DEF456" not in result[0]
        assert "store" in result[0]

    def test_removes_date_pattern(self):
        from app.ml.feature_extractor import DescriptionPreprocessor

        pp = DescriptionPreprocessor()
        pp.fit([])
        tx = SimpleNamespace(description="Payment on 2024-01-15 done")
        result = pp.transform([tx])
        assert "2024-01-15" not in result[0]
        assert "Payment" in result[0]

    def test_removes_structured_communication(self):
        from app.ml.feature_extractor import DescriptionPreprocessor

        pp = DescriptionPreprocessor()
        pp.fit([])
        tx = SimpleNamespace(description="Transfer ***123/4567/89012** ref")
        result = pp.transform([tx])
        assert "123/4567/89012" not in result[0]


class TestListModels:
    def test_list_empty(self, client, auth_headers, currency_eur):
        resp = client.get("/api/v2/ml/models", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_model(self, client, auth_headers, ml_model_valid):
        resp = client.get("/api/v2/ml/models", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["state"] == "valid"
        assert data[0]["filename"] == "test-model.pkl"


class TestTrainEndpoint:
    @patch("app.ml.trainer.train_model")
    def test_train_success(self, mock_train, client, auth_headers, currency_eur):
        mock_model = MagicMock()
        mock_model.id = 1
        mock_model.filename = "new-model.pkl"
        mock_model.state = "valid"
        mock_model.metadata_ = {"cv_score": 0.85}
        mock_train.return_value = mock_model

        resp = client.post("/api/v2/ml/train", headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["message"] == "Training complete"
        assert data["model"]["state"] == "valid"

    @patch("app.ml.trainer.train_model")
    def test_train_conflict(self, mock_train, client, auth_headers, currency_eur):
        from app.ml.trainer import ModelBeingTrainedError

        mock_train.side_effect = ModelBeingTrainedError("busy")

        resp = client.post("/api/v2/ml/train", headers=auth_headers)
        assert resp.status_code == 409

    @patch("app.ml.trainer.train_model")
    def test_train_not_enough_data(self, mock_train, client, auth_headers, currency_eur):
        from app.ml.trainer import NotEnoughDataError

        mock_train.side_effect = NotEnoughDataError("need more data")

        resp = client.post("/api/v2/ml/train", headers=auth_headers)
        assert resp.status_code == 400


class TestPredictEndpoint:
    @patch("app.ml.predictor.predict_categories")
    def test_predict_success(
        self, mock_predict, client, auth_headers, db, category_food, account_checking, currency_eur
    ):
        t = Transaction(
            external_id="pred-1",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("25.00"),
            id_currency=currency_eur.id,
            description="Grocery shopping",
            is_reviewed=False,
        )
        db.add(t)
        db.flush()

        mock_predict.return_value = [(category_food.id, 0.92)]

        resp = client.post(
            "/api/v2/ml/predict",
            headers=auth_headers,
            json={"transaction_ids": [t.id]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["predictions"]) == 1
        pred = data["predictions"][0]
        assert pred["category_id"] == category_food.id
        assert pred["category_name"] == "Food"
        assert pred["probability"] == 0.92

    def test_predict_empty_ids(self, client, auth_headers, currency_eur):
        resp = client.post(
            "/api/v2/ml/predict",
            headers=auth_headers,
            json={"transaction_ids": []},
        )
        assert resp.status_code == 200
        assert resp.json()["predictions"] == []

    @patch("app.ml.predictor.predict_categories")
    def test_predict_no_model(self, mock_predict, client, auth_headers, db, account_checking, currency_eur):
        from app.ml.predictor import NoValidModelError

        t = Transaction(
            external_id="pred-2",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("25.00"),
            id_currency=currency_eur.id,
            description="Test",
            is_reviewed=False,
        )
        db.add(t)
        db.flush()

        mock_predict.side_effect = NoValidModelError("no model")

        resp = client.post(
            "/api/v2/ml/predict",
            headers=auth_headers,
            json={"transaction_ids": [t.id]},
        )
        assert resp.status_code == 200
        assert resp.json()["predictions"] == []


class TestShouldTrain:
    def test_no_labeled_data(self, db, currency_eur):
        from app.ml.trainer import should_train

        assert should_train(db) is False

    def test_enough_data_no_model(self, db, category_food, account_checking, currency_eur):
        from app.ml.trainer import should_train

        for i in range(50):
            t = Transaction(
                external_id=f"st-{i}",
                id_source=account_checking.id,
                date=datetime.date(2024, 1, 1),
                amount=Decimal("10.00"),
                id_currency=currency_eur.id,
                description=f"Transaction {i}",
                is_reviewed=True,
            )
            db.add(t)
            db.flush()
            categorize(db, t, category_food)

        assert should_train(db) is True

    def test_skip_if_unchanged(self, db, category_food, account_checking, currency_eur):
        from app.ml.trainer import category_fingerprint, should_train

        for i in range(50):
            t = Transaction(
                external_id=f"su-{i}",
                id_source=account_checking.id,
                date=datetime.date(2024, 1, 1),
                amount=Decimal("10.00"),
                id_currency=currency_eur.id,
                description=f"Transaction {i}",
                is_reviewed=True,
            )
            db.add(t)
            db.flush()
            categorize(db, t, category_food)

        m = MLModel(
            filename="existing.pkl",
            state="valid",
            metadata_={"n_samples": 50, "category_fingerprint": category_fingerprint(db)},
        )
        db.add(m)
        db.flush()

        assert should_train(db) is False

    def test_retrain_on_new_labels(self, db, category_food, account_checking, currency_eur):
        from app.ml.trainer import category_fingerprint, should_train

        for i in range(50):
            t = Transaction(
                external_id=f"rn-{i}",
                id_source=account_checking.id,
                date=datetime.date(2024, 1, 1),
                amount=Decimal("10.00"),
                id_currency=currency_eur.id,
                description=f"Transaction {i}",
                is_reviewed=True,
            )
            db.add(t)
            db.flush()
            categorize(db, t, category_food)

        m = MLModel(
            filename="old.pkl",
            state="valid",
            metadata_={"n_samples": 40, "category_fingerprint": category_fingerprint(db)},
        )
        db.add(m)
        db.flush()

        assert should_train(db) is True

    def test_retrain_on_category_change(self, db, category_food, account_checking, currency_eur):
        from app.ml.trainer import should_train

        for i in range(50):
            t = Transaction(
                external_id=f"rc-{i}",
                id_source=account_checking.id,
                date=datetime.date(2024, 1, 1),
                amount=Decimal("10.00"),
                id_currency=currency_eur.id,
                description=f"Transaction {i}",
                is_reviewed=True,
            )
            db.add(t)
            db.flush()
            categorize(db, t, category_food)

        m = MLModel(
            filename="old.pkl",
            state="valid",
            metadata_={"n_samples": 50, "category_fingerprint": "stale-fingerprint"},
        )
        db.add(m)
        db.flush()

        assert should_train(db) is True


class TestPredictStaleCategory:
    @patch("app.ml.predictor.predict_categories")
    def test_stale_category_returns_null(self, mock_predict, client, auth_headers, db, account_checking, currency_eur):
        """When model predicts a category_id that no longer exists, return null."""
        t = Transaction(
            external_id="stale-1",
            id_source=account_checking.id,
            date=datetime.date(2024, 1, 1),
            amount=Decimal("25.00"),
            id_currency=currency_eur.id,
            description="Test stale",
            is_reviewed=False,
        )
        db.add(t)
        db.flush()

        mock_predict.return_value = [(99999, 0.85)]

        resp = client.post(
            "/api/v2/ml/predict",
            headers=auth_headers,
            json={"transaction_ids": [t.id]},
        )
        assert resp.status_code == 200
        pred = resp.json()["predictions"][0]
        assert pred["category_id"] is None
        assert pred["category_name"] is None
        assert pred["probability"] == 0.0
