from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Currency(Base):
    __tablename__ = "currency"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(15))
    short_name: Mapped[str] = mapped_column(String(255))
    long_name: Mapped[str] = mapped_column(String(255))
