from pydantic import BaseModel

from app.schemas.account import AccountResponse


class WalletAccountResponse(BaseModel):
    id_wallet: int
    id_account: int
    contribution_ratio: float
    account: AccountResponse

    model_config = {"from_attributes": True}


class WalletResponse(BaseModel):
    id: int
    name: str
    description: str | None
    accounts: list[WalletAccountResponse] = []

    model_config = {"from_attributes": True}


class WalletAccountInput(BaseModel):
    id_account: int
    contribution_ratio: float = 1.0


class WalletCreate(BaseModel):
    name: str
    description: str | None = None
    accounts: list[WalletAccountInput] = []


class WalletUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    accounts: list[WalletAccountInput] | None = None
