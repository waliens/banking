from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: int
    name: str
    id_parent: int | None
    color: str | None
    icon: str | None
    sort_order: int
    is_income: bool

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
    id_parent: int | None = None
    color: str
    icon: str | None = None
    sort_order: int = 0
    is_income: bool = False


class CategoryUpdate(BaseModel):
    name: str | None = None
    id_parent: int | None = None
    color: str | None = None
    icon: str | None = None
    sort_order: int | None = None
    is_income: bool | None = None
