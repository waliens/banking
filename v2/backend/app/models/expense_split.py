from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseSplit(Base):
    __tablename__ = "expense_split"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    id_payment_transaction: Mapped[int] = mapped_column(ForeignKey("transaction.id"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    my_share: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending")

    payment_transaction: Mapped["Transaction"] = relationship(lazy="joined")
    reimbursements: Mapped[list["ExpenseSplitReimbursement"]] = relationship(back_populates="split", lazy="selectin")


class ExpenseSplitReimbursement(Base):
    __tablename__ = "expense_split_reimbursement"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_split: Mapped[int] = mapped_column(ForeignKey("expense_split.id", ondelete="CASCADE"))
    id_transaction: Mapped[int] = mapped_column(ForeignKey("transaction.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))

    split: Mapped["ExpenseSplit"] = relationship(back_populates="reimbursements")
    transaction: Mapped["Transaction"] = relationship(lazy="joined")


from app.models.transaction import Transaction  # noqa: E402
