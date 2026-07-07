from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AlarmLog(Base):
    __tablename__ = "alarm_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        index=True,
        nullable=False,
    )
    alarm_type: Mapped[str] = mapped_column(String(50), nullable=False)
    alarm_level: Mapped[str] = mapped_column(String(20), default="warning", nullable=False)
    alarm_content: Mapped[str] = mapped_column(String(500), nullable=False)
    handled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
