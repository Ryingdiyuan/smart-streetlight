from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.models.light_data import LightData
from app.schemas.light_data import LightDataCreate, LightDataRead

router = APIRouter(prefix="/devices/{device_id}", tags=["light-data"])


def ensure_device_exists(db: Session, device_id: int) -> None:
    if db.get(Device, device_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在",
        )


@router.post(
    "/light-data",
    response_model=LightDataRead,
    status_code=status.HTTP_201_CREATED,
)
def create_light_data(
    device_id: int,
    light_data_create: LightDataCreate,
    db: Session = Depends(get_db),
) -> LightData:
    ensure_device_exists(db, device_id)

    light_data = LightData(
        device_id=device_id,
        light_intensity=light_data_create.light_intensity,
        lamp_status=light_data_create.lamp_status,
        voltage=light_data_create.voltage,
        reported_at=light_data_create.reported_at or datetime.utcnow(),
    )
    db.add(light_data)
    db.commit()
    db.refresh(light_data)
    return light_data


@router.get("/latest-light", response_model=LightDataRead)
def get_latest_light_data(
    device_id: int,
    db: Session = Depends(get_db),
) -> LightData:
    ensure_device_exists(db, device_id)

    light_data = (
        db.query(LightData)
        .filter(LightData.device_id == device_id)
        .order_by(LightData.reported_at.desc(), LightData.id.desc())
        .first()
    )
    if light_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无光照数据",
        )
    return light_data


@router.get("/light-history", response_model=list[LightDataRead])
def list_light_history(
    device_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
) -> list[LightData]:
    ensure_device_exists(db, device_id)

    query = db.query(LightData).filter(LightData.device_id == device_id)
    if start_time is not None:
        query = query.filter(LightData.reported_at >= start_time)
    if end_time is not None:
        query = query.filter(LightData.reported_at <= end_time)

    return (
        query.order_by(LightData.reported_at.desc(), LightData.id.desc())
        .limit(limit)
        .all()
    )
