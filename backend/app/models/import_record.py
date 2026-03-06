import datetime

from sqlalchemy import Date, DateTime, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ImportRecord(Base):
    __tablename__ = "import_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    format: Mapped[str] = mapped_column(String(50))
    filenames: Mapped[list[str]] = mapped_column(JSON, default=list)
    total_transactions: Mapped[int] = mapped_column(default=0)
    new_transactions: Mapped[int] = mapped_column(default=0)
    duplicate_transactions: Mapped[int] = mapped_column(default=0)
    skipped_transactions: Mapped[int] = mapped_column(default=0)
    new_accounts: Mapped[int] = mapped_column(default=0)
    auto_tagged: Mapped[int] = mapped_column(default=0)
    date_earliest: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    date_latest: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
