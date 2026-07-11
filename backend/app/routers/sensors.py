from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin, require_user_or_above
from app.models.device import Device
from app.models.sensor import Sensor
from app.schemas.sensor import SensorCreate, SensorRead, SensorUpdate

router = APIRouter(prefix="/sensors", tags=["sensors"])


def get_sensor_or_404(db: Session, sensor_id: int) -> Sensor:
    sensor = db.get(Sensor, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="传感器不存在")
    return sensor


def get_bound_device(db: Session, sensor_id: int) -> Device | None:
    return db.query(Device).filter(Device.sensor_id == sensor_id).first()


def ensure_sensor_code_unique(db: Session, sensor_code: str, exclude_id: int | None = None) -> None:
    query = db.query(Sensor).filter(Sensor.sensor_code == sensor_code)
    if exclude_id is not None:
        query = query.filter(Sensor.id != exclude_id)
    if query.first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="传感器编码已存在")


def serialize_sensor(db: Session, sensor: Sensor) -> dict:
    bound_device = get_bound_device(db, sensor.id)
    return {
        "id": sensor.id,
        "sensor_code": sensor.sensor_code,
        "sensor_name": sensor.sensor_name,
        "location": sensor.location,
        "latitude": sensor.latitude,
        "longitude": sensor.longitude,
        "status": sensor.status,
        "online": sensor.online,
        "base_light": sensor.base_light,
        "variance": sensor.variance,
        "voltage_base": sensor.voltage_base,
        "telemetry_enabled": sensor.telemetry_enabled,
        "telemetry_interval_seconds": sensor.telemetry_interval_seconds,
        "status_every": sensor.status_every,
        "last_heartbeat_at": sensor.last_heartbeat_at,
        "bound_device_id": bound_device.id if bound_device else None,
        "bound_device_code": bound_device.device_code if bound_device else None,
        "bound_device_name": bound_device.device_name if bound_device else None,
    }


@router.get("", response_model=list[SensorRead])
def list_sensors(
    only_unbound: bool = Query(default=False),
    only_online: bool = Query(default=False),
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
) -> list[dict]:
    sensors = (
        db.query(Sensor)
        .filter(Sensor.deleted_at.is_(None))
        .order_by(Sensor.id.asc())
        .all()
    )
    items = [serialize_sensor(db, sensor) for sensor in sensors]
    if only_unbound:
        items = [item for item in items if item["bound_device_id"] is None]
    if only_online:
        items = [
            item
            for item in items
            if item["online"] and str(item["status"]).lower() == "online"
        ]
    return items


@router.post("", response_model=SensorRead, status_code=status.HTTP_201_CREATED)
def create_sensor(
    sensor_create: SensorCreate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    ensure_sensor_code_unique(db, sensor_create.sensor_code)
    sensor = Sensor(**sensor_create.model_dump())
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return serialize_sensor(db, sensor)


@router.put("/{sensor_id}", response_model=SensorRead)
def update_sensor(
    sensor_id: int,
    sensor_update: SensorUpdate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    sensor = get_sensor_or_404(db, sensor_id)
    update_data = sensor_update.model_dump(exclude_unset=True)

    if "sensor_code" in update_data:
        ensure_sensor_code_unique(db, update_data["sensor_code"], exclude_id=sensor_id)

    for field, value in update_data.items():
        setattr(sensor, field, value)

    db.commit()
    db.refresh(sensor)
    return serialize_sensor(db, sensor)


@router.delete("/{sensor_id}")
def delete_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict[str, str]:
    sensor = get_sensor_or_404(db, sensor_id)
    bound_device = get_bound_device(db, sensor_id)
    if bound_device is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"传感器已绑定路灯 {bound_device.device_code}，请先解绑",
        )

    db.delete(sensor)
    db.commit()
    return {"message": "删除成功"}
