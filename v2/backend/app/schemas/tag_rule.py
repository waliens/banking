"""Pydantic schemas for tag rule endpoints."""

import re
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.category import CategoryResponse


def _validate_regex(v: str | None) -> str | None:
    if v is not None:
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    return v


class TagRuleBase(BaseModel):
    name: str
    id_category: int
    match_description: str | None = None
    match_amount_min: Decimal | None = None
    match_amount_max: Decimal | None = None
    match_account_from: int | None = None
    match_account_to: int | None = None
    is_active: bool = True
    priority: int = 0

    @field_validator("match_description")
    @classmethod
    def validate_regex(cls, v: str | None) -> str | None:
        return _validate_regex(v)


class TagRuleCreate(TagRuleBase):
    pass


class TagRuleUpdate(BaseModel):
    name: str | None = None
    id_category: int | None = None
    match_description: str | None = None
    match_amount_min: Decimal | None = None
    match_amount_max: Decimal | None = None
    match_account_from: int | None = None
    match_account_to: int | None = None
    is_active: bool | None = None
    priority: int | None = None

    @field_validator("match_description")
    @classmethod
    def validate_regex(cls, v: str | None) -> str | None:
        return _validate_regex(v)


class TagRuleResponse(BaseModel):
    id: int
    name: str
    id_category: int
    match_description: str | None = None
    match_amount_min: Decimal | None = None
    match_amount_max: Decimal | None = None
    match_account_from: int | None = None
    match_account_to: int | None = None
    is_active: bool
    priority: int
    category: CategoryResponse

    model_config = {"from_attributes": True}


class TagRuleApplyResponse(BaseModel):
    applied_count: int
