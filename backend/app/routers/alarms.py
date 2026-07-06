from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_maintainer_or_admin, require_user_or_above
from app.models.alarm_log import AlarmLog
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


@router.get("", response_model=list[AlarmLogRead])
def list_alarms(
    handled: bool | None = None,
    alarm_type: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
) -> list[AlarmLog]:
    query = db.query(AlarmLog)

    if handled is not None:
        query = query.filter(AlarmLog.handled.is_(handled))
    if alarm_type is not None:
        query = query.filter(AlarmLog.alarm_type == alarm_type)

    return query.order_by(AlarmLog.created_at.desc(), AlarmLog.id.desc()).limit(limit).all()


@router.get("/{alarm_id}", response_model=AlarmLogRead)
def get_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
) -> AlarmLog:
    return get_alarm_or_404(db, alarm_id)


@router.put("/{alarm_id}/handle", response_model=AlarmLogRead)
def handle_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_maintainer_or_admin),
) -> AlarmLog:
    alarm = get_alarm_or_404(db, alarm_id)
    alarm.handled = True
    alarm.handled_at = datetime.utcnow()
    db.commit()
    db.refresh(alarm)
    return alarm
