from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_maintainer_or_admin, require_user_or_above
from app.models.alarm_log import AlarmLog
from app.models.device import Device
from app.models.sensor import Sensor
from app.schemas.alarm_log import AlarmLogRead

router = APIRouter(prefix="/alarms", tags=["alarms"])


def get_alarm_or_404(db: Session, alarm_id: int) -> AlarmLog:
    alarm = db.get(AlarmLog, alarm_id)
    if alarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警不存在",
        )
    return alarm


def serialize_alarm(db: Session, alarm: AlarmLog) -> dict:
    device = db.get(Device, alarm.device_id) if alarm.device_id is not None else None
    sensor = db.get(Sensor, alarm.sensor_id) if alarm.sensor_id is not None else None
    return {
        "id": alarm.id,
        "device_id": alarm.device_id,
        "sensor_id": alarm.sensor_id,
        "device_code": device.device_code if device is not None else None,
        "sensor_code": sensor.sensor_code if sensor is not None else None,
        "sensor_name": sensor.sensor_name if sensor is not None else None,
        "alarm_type": alarm.alarm_type,
        "alarm_level": alarm.alarm_level,
        "alarm_content": alarm.alarm_content,
        "handled": alarm.handled,
        "handled_at": alarm.handled_at,
        "created_at": alarm.created_at,
    }


@router.get("", response_model=list[AlarmLogRead])
def list_alarms(
    handled: bool | None = None,
    alarm_type: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
) -> list[dict]:
    query = db.query(AlarmLog)

    if handled is not None:
        query = query.filter(AlarmLog.handled.is_(handled))
    if alarm_type is not None:
        query = query.filter(AlarmLog.alarm_type == alarm_type)

    alarms = query.order_by(AlarmLog.created_at.desc(), AlarmLog.id.desc()).limit(limit).all()
    return [serialize_alarm(db, alarm) for alarm in alarms]


@router.get("/{alarm_id}", response_model=AlarmLogRead)
def get_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
) -> dict:
    return serialize_alarm(db, get_alarm_or_404(db, alarm_id))


@router.put("/{alarm_id}/handle", response_model=AlarmLogRead)
def handle_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_maintainer_or_admin),
) -> dict:
    alarm = get_alarm_or_404(db, alarm_id)
    alarm.handled = True
    alarm.handled_at = datetime.utcnow()
    db.commit()
    db.refresh(alarm)
    return serialize_alarm(db, alarm)
