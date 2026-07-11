import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.alarm_log import AlarmLog
from app.models.device import Device
from app.models.sensor import Sensor

logger = logging.getLogger(__name__)


def create_offline_alarm_if_needed(
    db: Session,
    sensor: Sensor,
    bound_device: Device | None = None,
) -> AlarmLog | None:
    existing_alarm = (
        db.query(AlarmLog)
        .filter(
            AlarmLog.sensor_id == sensor.id,
            AlarmLog.alarm_type == "offline",
            AlarmLog.handled.is_(False),
        )
        .first()
    )
    if existing_alarm is not None:
        return None

    alarm = AlarmLog(
        device_id=bound_device.id if bound_device is not None else None,
        sensor_id=sensor.id,
        alarm_type="offline",
        alarm_level="warning",
        alarm_content=f"传感器 {sensor.sensor_code} 已离线",
        handled=False,
    )
    db.add(alarm)
    return alarm


def run_offline_check() -> None:
    db = SessionLocal()
    try:
        deadline = datetime.now() - timedelta(seconds=settings.device_offline_seconds)
        offline_sensors = (
            db.query(Sensor)
            .filter(
                Sensor.status == "online",
                Sensor.last_heartbeat_at.isnot(None),
                Sensor.last_heartbeat_at < deadline,
            )
            .all()
        )

        for sensor in offline_sensors:
            sensor.status = "offline"
            bound_device = db.query(Device).filter(Device.sensor_id == sensor.id).first()
            if bound_device is not None:
                bound_device.status = "offline"
                bound_device.last_heartbeat_at = sensor.last_heartbeat_at
            create_offline_alarm_if_needed(db, sensor, bound_device)

        db.commit()
        if offline_sensors:
            logger.info("Marked %s sensor(s) offline", len(offline_sensors))
    except Exception:
        db.rollback()
        logger.exception("Failed to check offline sensors")
    finally:
        db.close()
