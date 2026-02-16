"""Pydantic schemas for tag rule endpoints."""

from decimal import Decimal

from pydantic import BaseModel

from app.schemas.category import CategoryResponse


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
