from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ThresholdConfig(Base):
    __tablename__ = "threshold_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        unique=True,
        index=True,
        nullable=False,
    )
    low_threshold: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    high_threshold: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
