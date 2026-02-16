"""Pydantic schemas for ML endpoints."""

from typing import Any

from pydantic import BaseModel


class MLModelResponse(BaseModel):
    id: int
    filename: str
    metadata_: dict[str, Any] | None = None
    state: str

    model_config = {"from_attributes": True}


class TrainResponse(BaseModel):
    model: MLModelResponse
    message: str


class PredictRequest(BaseModel):
    transaction_ids: list[int]


class PredictionItem(BaseModel):
    transaction_id: int
    category_id: int | None
    category_name: str | None
    category_color: str | None
    probability: float


class PredictResponse(BaseModel):
    predictions: list[PredictionItem]
