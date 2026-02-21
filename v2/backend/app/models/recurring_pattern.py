import datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RecurringPattern(Base):
    __tablename__ = "recurring_pattern"

    id: Mapped[int] = mapped_column(primary_key=True)
    description_pattern: Mapped[str] = mapped_column(String(500))
    id_category: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    typical_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    frequency_days: Mapped[int | None] = mapped_column()
    last_seen_date: Mapped[datetime.date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(default=True)

    category: Mapped["Category | None"] = relationship(lazy="joined")


from app.models.category import Category  # noqa: E402
