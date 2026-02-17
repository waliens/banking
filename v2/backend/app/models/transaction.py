import datetime
from decimal import Decimal

from typing import Any

from sqlalchemy import Date, ForeignKey, Index, JSON, Numeric, String, Text
from sqlalchemy import types as sa_types
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TSVector(sa_types.TypeDecorator[str]):
    """A type that renders as TSVECTOR on PostgreSQL and TEXT elsewhere (e.g. SQLite for tests)."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> sa_types.TypeEngine[Any]:
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import TSVECTOR

            return dialect.type_descriptor(TSVECTOR())
        return dialect.type_descriptor(Text())


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    id_source: Mapped[int | None] = mapped_column(ForeignKey("account.id"))
    id_dest: Mapped[int | None] = mapped_column(ForeignKey("account.id"))
    date: Mapped[datetime.date] = mapped_column(Date)
    raw_metadata: Mapped[dict[str, object] | None] = mapped_column("raw_metadata", JSON)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    id_currency: Mapped[int] = mapped_column(ForeignKey("currency.id"))
    id_category: Mapped[int | None] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"))
    data_source: Mapped[str | None] = mapped_column(String(50))
    id_duplicate_of: Mapped[int | None] = mapped_column(ForeignKey("transaction.id"))
    description: Mapped[str] = mapped_column(String, default="", server_default="")
    is_reviewed: Mapped[bool] = mapped_column(default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(String)
    search_text: Mapped[str | None] = mapped_column(TSVector())
    id_recurring: Mapped[int | None] = mapped_column(ForeignKey("recurring_pattern.id"))
    id_transaction_group: Mapped[int | None] = mapped_column(
        ForeignKey("transaction_group.id", ondelete="SET NULL"), nullable=True
    )
    effective_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)

    source: Mapped["Account | None"] = relationship(foreign_keys=[id_source], lazy="joined")
    dest: Mapped["Account | None"] = relationship(foreign_keys=[id_dest], lazy="joined")
    currency: Mapped["Currency"] = relationship(lazy="joined")
    category: Mapped["Category | None"] = relationship(lazy="joined")
    duplicate_of: Mapped["Transaction | None"] = relationship(remote_side=[id])
    transaction_group: Mapped["TransactionGroup | None"] = relationship(back_populates="transactions", lazy="joined")

    __table_args__ = (Index("ix_transaction_date", "date"),)


from app.models.account import Account  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.currency import Currency  # noqa: E402
from app.models.transaction_group import TransactionGroup  # noqa: E402
