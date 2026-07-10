from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    sensor_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    sensor_name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255), default=None)
    latitude: Mapped[float | None] = mapped_column(Float, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, default=None)
    status: Mapped[str] = mapped_column(String(20), default="offline")
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    online: Mapped[bool] = mapped_column(Boolean, default=True)
    base_light: Mapped[int] = mapped_column(Integer, default=120)
    variance: Mapped[int] = mapped_column(Integer, default=35)
    voltage_base: Mapped[float] = mapped_column(Float, default=220.5)
    telemetry_interval_seconds: Mapped[int] = mapped_column(Integer, default=5)
    status_every: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
