import uuid

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MLModel(Base):
    __tablename__ = "ml_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)
    state: Mapped[str] = mapped_column(String(20))  # valid, invalid, training, deleted

    @staticmethod
    def generate_filename() -> str:
        return f"{uuid.uuid4()}.pkl"
