from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Wallet(Base):
    __tablename__ = "wallet"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1024))

    accounts: Mapped[list["WalletAccount"]] = relationship(
        back_populates="wallet", lazy="joined", cascade="all, delete-orphan"
    )


class WalletAccount(Base):
    __tablename__ = "wallet_account"

    id_wallet: Mapped[int] = mapped_column(ForeignKey("wallet.id", ondelete="CASCADE"), primary_key=True)
    id_account: Mapped[int] = mapped_column(ForeignKey("account.id"), primary_key=True)
    contribution_ratio: Mapped[float] = mapped_column(default=1.0)

    wallet: Mapped["Wallet"] = relationship(back_populates="accounts")
    account: Mapped["Account"] = relationship(lazy="joined")


from app.models.account import Account  # noqa: E402
