from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LightData(Base):
    __tablename__ = "light_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        index=True,
        nullable=False,
    )
    light_intensity: Mapped[int] = mapped_column(Integer, nullable=False)
    lamp_status: Mapped[str] = mapped_column(String(20), nullable=False)
    voltage: Mapped[float | None] = mapped_column(Float, default=None)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
