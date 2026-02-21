from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str | None] = mapped_column(String(63))
    name: Mapped[str | None] = mapped_column(String(255))
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    id_currency: Mapped[int] = mapped_column(ForeignKey("currency.id"))
    institution: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(default=True)

    currency: Mapped["Currency"] = relationship(lazy="joined")
    aliases: Mapped[list["AccountAlias"]] = relationship(back_populates="account", lazy="joined")

    __table_args__ = (UniqueConstraint("number", "name", name="account_name_number_unique_constraint"),)


class AccountAlias(Base):
    __tablename__ = "account_alias"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str | None] = mapped_column(String(63))
    name: Mapped[str | None] = mapped_column(String(255))
    id_account: Mapped[int] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))

    account: Mapped["Account"] = relationship(back_populates="aliases")


# resolve forward ref
from app.models.currency import Currency  # noqa: E402
