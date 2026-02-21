from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionGroup(Base):
    __tablename__ = "transaction_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="transaction_group")


from app.models.transaction import Transaction  # noqa: E402
