from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CategorySplit(Base):
    __tablename__ = "category_split"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_transaction: Mapped[int | None] = mapped_column(
        ForeignKey("transaction.id", ondelete="CASCADE"), nullable=True
    )
    id_group: Mapped[int | None] = mapped_column(
        ForeignKey("transaction_group.id", ondelete="CASCADE"), nullable=True
    )
    id_category: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))

    transaction: Mapped["Transaction | None"] = relationship(
        foreign_keys=[id_transaction], back_populates="category_splits"
    )
    group: Mapped["TransactionGroup | None"] = relationship(
        foreign_keys=[id_group], back_populates="category_splits"
    )
    category: Mapped["Category"] = relationship(lazy="joined")


from app.models.transaction import Transaction  # noqa: E402
from app.models.transaction_group import TransactionGroup  # noqa: E402
from app.models.category import Category  # noqa: E402
