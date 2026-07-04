import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.alarm_log import AlarmLog
from app.models.device import Device

logger = logging.getLogger(__name__)


def create_offline_alarm_if_needed(db: Session, device: Device) -> AlarmLog | None:
    existing_alarm = (
        db.query(AlarmLog)
        .filter(
            AlarmLog.device_id == device.id,
            AlarmLog.alarm_type == "offline",
            AlarmLog.handled.is_(False),
        )
        .first()
    )
    if existing_alarm is not None:
        return None

    alarm = AlarmLog(
        device_id=device.id,
        alarm_type="offline",
        alarm_level="warning",
        alarm_content=f"设备 {device.device_code} 已离线",
        handled=False,
    )
    db.add(alarm)
    return alarm


def run_offline_check() -> None:
    db = SessionLocal()
    try:
        deadline = datetime.utcnow() - timedelta(seconds=settings.device_offline_seconds)
        offline_devices = (
            db.query(Device)
            .filter(
                Device.status == "online",
                Device.last_heartbeat_at.isnot(None),
                Device.last_heartbeat_at < deadline,
            )
            .all()
        )

        for device in offline_devices:
            device.status = "offline"
            create_offline_alarm_if_needed(db, device)

        db.commit()
        if offline_devices:
            logger.info("Marked %s device(s) offline", len(offline_devices))
    except Exception:
        db.rollback()
        logger.exception("Failed to check offline devices")
    finally:
        db.close()
