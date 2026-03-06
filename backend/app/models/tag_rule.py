from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TagRule(Base):
    __tablename__ = "tag_rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    id_category: Mapped[int] = mapped_column(ForeignKey("category.id"))
    match_description: Mapped[str | None] = mapped_column(String(500))
    match_amount_min: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    match_amount_max: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    match_account_from: Mapped[int | None] = mapped_column(ForeignKey("account.id"))
    match_account_to: Mapped[int | None] = mapped_column(ForeignKey("account.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    priority: Mapped[int] = mapped_column(default=0)

    category: Mapped["Category"] = relationship(lazy="joined")


from app.models.category import Category  # noqa: E402
