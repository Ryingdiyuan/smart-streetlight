from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    device_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    device_name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255), default=None)
    latitude: Mapped[float | None] = mapped_column(Float, default=None, comment="GPS 纬度")
    longitude: Mapped[float | None] = mapped_column(Float, default=None, comment="GPS 经度")
    status: Mapped[str] = mapped_column(String(20), default="offline")
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
