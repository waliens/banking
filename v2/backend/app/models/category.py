from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    id_parent: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    color: Mapped[str | None] = mapped_column(String(255))
    icon: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(default=0)
    is_income: Mapped[bool] = mapped_column(default=False)
