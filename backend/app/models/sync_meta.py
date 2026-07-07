from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SyncMeta(Base):
    """Track per-table sync progress for cloud-to-local replication."""

    __tablename__ = "db_sync_meta"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    last_synced_id: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
