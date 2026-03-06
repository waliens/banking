import datetime

from pydantic import BaseModel


class ImportRecordResponse(BaseModel):
    id: int
    created_at: datetime.datetime
    format: str
    filenames: list[str]
    total_transactions: int
    new_transactions: int
    duplicate_transactions: int
    skipped_transactions: int
    new_accounts: int
    auto_tagged: int
    date_earliest: datetime.date | None
    date_latest: datetime.date | None

    model_config = {"from_attributes": True}
