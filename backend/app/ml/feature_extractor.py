"""Feature extraction for ML categorization pipeline.

Ported from server/ml/feature_extractor.py with v2 adaptations:
- Uses hardcoded stopwords instead of nltk
- v2 field names (date, raw_metadata)
- CategoryEncoder uses SQLAlchemy query directly
"""

import re
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sqlalchemy.orm import Session

from app.ml.stopwords import STOPWORDS
from app.models.category import Category

REGEX_IBAN = r"[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}(?:\s?\d{0,4})?"

REMOVE_PATTERNS = [
    # belfius specifics
    r"REF\. : [0-9A-Z]{9,13}",
    r"VAL\. [0-9]{0,2}-[0-9]{0,2}",
    r"LE [0-9]{0,2}/[0-9]{0,2} [0-9]{0,2}:[0-9]{0,2}",
    r"\bN\. (?:[A-Z]+)?[0-9-]+\b",
    # ing specifics
    r"R\u00e9f\u00e9rence ING: COP[0-9]{11}",
    r"Carte: [0-9]{3}-[0-9]{7}-[0-9]{2}-[0-9]{4}",
    # dates/times
    r"\b(?:[0-9]{4}|[0-9]{2})[-/][0-9]{2}[-/](?:[0-9]{4}|[0-9]{2})\b",
    r"\b(?:[0-9]{4}|[0-9]{2})[-/](?:[0-9]{4}|[0-9]{2})\b",
    r"\b(?:[0-2]?[0-9]h[0-9]{2}|[0-2][0-9]:[0-9]{2}(?::[0-9]{2})?)\b",
    # IBAN/card number
    REGEX_IBAN,
    r"\b[0-9X]{4}\s*[0-9X]{4}\s*[0-9X]{4}\s*[0-9X]{4}(?:\s*[0-9X])?\b",
    # structured communication
    r"(\*\*)?[0-9]{3}/[0-9]{4}/[0-9]{5}(\*\*)?",
]


class DescriptionPreprocessor(BaseEstimator, TransformerMixin):
    """Removes noise patterns from transaction descriptions."""

    def __init__(self, remove_patterns: list[str] | None = None) -> None:
        self.remove_patterns = remove_patterns or REMOVE_PATTERNS
        self._compiled: list[re.Pattern[str]] = []

    def fit(self, X: Any, y: Any = None) -> "DescriptionPreprocessor":
        self._compiled = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.remove_patterns]
        return self

    def transform(self, X: Any, y: Any = None) -> list[str]:
        return [self._clean(t) for t in X]

    def _clean(self, transaction: Any) -> str:
        val = str(transaction.description)
        for pattern in self._compiled:
            val = re.sub(pattern, "", val)
        return val


class DescriptionEncoder(BaseEstimator, TransformerMixin):
    """TF-IDF encoding of preprocessed transaction descriptions."""

    def __init__(self) -> None:
        self._preprocessor = DescriptionPreprocessor()
        self._tfidf = TfidfVectorizer(
            decode_error="replace",
            strip_accents="unicode",
            stop_words=list(STOPWORDS),
            max_df=0.9,
            min_df=2,
        )
        self._pipeline = Pipeline([("desc-preprocess", self._preprocessor), ("tfidf", self._tfidf)])

    def fit(self, X: Any, y: Any = None) -> "DescriptionEncoder":
        self._pipeline.fit(X)
        return self

    def transform(self, X: Any, y: Any = None) -> Any:
        return self._pipeline.transform(X)


class DateTransformer(BaseEstimator, TransformerMixin):
    """Extracts [year, month, day, weekday] from transaction.date."""

    def fit(self, X: Any, y: Any = None) -> "DateTransformer":
        return self

    def transform(self, X: Any, y: Any = None) -> list[list[int]]:
        return [self._date_features(t) for t in X]

    @staticmethod
    def _date_features(transaction: Any) -> list[int]:
        d = transaction.date
        if d is None:
            return [-1, -1, -1, -1]
        return [d.year, d.month, d.day, d.weekday()]


class AccountsOneHot(BaseEstimator, TransformerMixin):
    """One-hot encodes id_source and id_dest."""

    def __init__(self) -> None:
        self._encoder = OneHotEncoder(handle_unknown="ignore")

    def fit(self, X: Any, y: Any = None) -> "AccountsOneHot":
        self._encoder.fit(self._accounts(X))
        return self

    def transform(self, X: Any, y: Any = None) -> Any:
        return self._encoder.transform(self._accounts(X)).toarray()

    @staticmethod
    def _accounts(X: Any) -> np.ndarray:
        return np.array(
            [[t.id_source if t.id_source is not None else -1, t.id_dest if t.id_dest is not None else -1] for t in X]
        )


class HourMinuteTransformer(BaseEstimator, TransformerMixin):
    """Extracts hour and minute from description text."""

    PATTERN_ISO = re.compile(r".*([0-9]{2}):([0-9]{2})(?::[0-9]{2})?.*")
    PATTERN_HOUR = re.compile(r".*([0-2]?[0-9])h([0-5][0-9]).*")

    def fit(self, X: Any, y: Any = None) -> "HourMinuteTransformer":
        return self

    def transform(self, X: Any, y: Any = None) -> list[list[int]]:
        return [self._extract_time(t) for t in X]

    def _extract_time(self, transaction: Any) -> list[int]:
        for pattern in [self.PATTERN_ISO, self.PATTERN_HOUR]:
            match = re.match(pattern, transaction.description)
            if match is not None:
                return [int(match.group(1)), int(match.group(2))]
        return [-1, -1]


class SingleFeatureTransformer(BaseEstimator, TransformerMixin):
    """Extracts a single scalar feature (amount)."""

    def fit(self, X: Any, y: Any = None) -> "SingleFeatureTransformer":
        return self

    def transform(self, X: Any, y: Any = None) -> list[list[float]]:
        return [[float(t.amount)] for t in X]


class CategoryEncoder:
    """Maps leaf category IDs to parent-level IDs at fine or coarse granularity."""

    def __init__(self, db: Session, level: str = "fine") -> None:
        if level not in {"fine", "coarse"}:
            raise ValueError(f"unknown category encoder level '{level}'")
        self._level = level
        self._categories = db.query(Category).all()
        self._children: dict[int | None, list[Category]] = {}
        for c in self._categories:
            self._children.setdefault(c.id_parent, []).append(c)
        self._category_map = {c.id: c for c in self._categories}

        self._tag_index = self._build_index()
        self._tag_inv_index = {leaf: parent for parent, leaves in self._tag_index.items() for leaf in leaves}
        self._label_encoder = LabelEncoder()
        self._label_encoder.fit(list(self._tag_index.keys()))

    def _build_index(self) -> dict[int, set[int]]:
        result: dict[int, set[int]] = {}
        for root in self._children.get(None, []):
            result.update(self._build_index_recur(root, 0))
        return result

    def _build_index_recur(self, category: Category, depth: int) -> dict[int, set[int]]:
        children_ids = [c.id for c in self._children.get(category.id, [])]
        if not children_ids:
            return {category.id: {category.id}}
        if (depth == 1 and self._level == "coarse") or (depth == 2 and self._level == "fine"):
            all_descendants = self._get_all_descendants(category.id)
            return {category.id: {category.id} | all_descendants}
        result: dict[int, set[int]] = {}
        for child in self._children.get(category.id, []):
            result.update(self._build_index_recur(child, depth + 1))
        return result

    def _get_all_descendants(self, category_id: int) -> set[int]:
        descendants: set[int] = set()
        for child in self._children.get(category_id, []):
            descendants.add(child.id)
            descendants |= self._get_all_descendants(child.id)
        return descendants

    def transform(self, category_ids: Any) -> Any:
        mapped = [self._tag_inv_index[cid] for cid in category_ids]
        return self._label_encoder.transform(mapped)

    def inverse_transform(self, encoded: Any) -> Any:
        return self._label_encoder.inverse_transform(encoded)


def bank_csv_transformer() -> FeatureUnion:
    """Build the feature union for bank CSV transaction data."""
    return FeatureUnion(
        [
            ("desc-tf-idf", DescriptionEncoder()),
            ("when-to-scalars", DateTransformer()),
            ("accounts-one-hot", AccountsOneHot()),
            ("hour-minute-extractor", HourMinuteTransformer()),
            ("amount-extractor", SingleFeatureTransformer()),
        ]
    )
