import datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    data_source: Mapped[str | None] = mapped_column(String(50))
    id_duplicate_of: Mapped[int | None] = mapped_column(ForeignKey("transaction.id"))
    description: Mapped[str] = mapped_column(String, default="", server_default="")
    is_reviewed: Mapped[bool] = mapped_column(default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(String)
    id_transaction_group: Mapped[int | None] = mapped_column(
        ForeignKey("transaction_group.id", ondelete="SET NULL"), nullable=True
    )
    effective_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    id_import: Mapped[int | None] = mapped_column(ForeignKey("import_record.id"), nullable=True)
    auto_tagged_at_import: Mapped[bool] = mapped_column(default=False, server_default="false")

    source: Mapped["Account | None"] = relationship(foreign_keys=[id_source], lazy="joined")
    dest: Mapped["Account | None"] = relationship(foreign_keys=[id_dest], lazy="joined")
    currency: Mapped["Currency"] = relationship(lazy="joined")
    duplicate_of: Mapped["Transaction | None"] = relationship(remote_side=[id])
    transaction_group: Mapped["TransactionGroup | None"] = relationship(back_populates="transactions", lazy="joined")
    category_splits: Mapped[list["CategorySplit"]] = relationship(
        foreign_keys="CategorySplit.id_transaction",
        back_populates="transaction",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_transaction_date", "date"),)


from app.models.account import Account  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.category_split import CategorySplit  # noqa: E402
from app.models.currency import Currency  # noqa: E402
from app.models.transaction_group import TransactionGroup  # noqa: E402
