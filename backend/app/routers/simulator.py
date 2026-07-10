from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_admin
from app.models.device import Device
from app.models.sensor import Sensor
from app.mqtt.client import mqtt_client
from app.schemas.sensor import SensorCreate
from app.schemas.simulator import (
    SimulatorConfigRead,
    SimulatorConfigUpdate,
    SimulatorLogRead,
    SimulatorSensorCreate,
    SimulatorSensorRead,
    SimulatorSensorUpdate,
)
from app.services.simulator_service import simulator_manager

router = APIRouter(prefix="/simulator", tags=["simulator"])


def list_all_sensors(db: Session) -> list[Sensor]:
    return db.query(Sensor).order_by(Sensor.id.asc()).all()


def build_bound_device_map(db: Session) -> dict[int, Device]:
    devices = db.query(Device).filter(Device.sensor_id.is_not(None)).all()
    return {device.sensor_id: device for device in devices if device.sensor_id is not None}


def sync_sensor_connection_state(
    db: Session,
    sensor: Sensor,
    *,
    online: bool,
    heartbeat_at: datetime | None = None,
) -> None:
    heartbeat_time = heartbeat_at or datetime.utcnow()
    sensor.status = "online" if online else "offline"
    sensor.last_heartbeat_at = heartbeat_time

    bound_device = db.query(Device).filter(Device.sensor_id == sensor.id).first()
    if bound_device is not None:
        bound_device.status = sensor.status
        bound_device.last_heartbeat_at = heartbeat_time


def sync_sensors_snapshot(db: Session) -> list[dict]:
    return simulator_manager.sync_sensors(list_all_sensors(db), build_bound_device_map(db))


def get_sensor_or_404(db: Session, sensor_id: int) -> Sensor:
    sensor = db.get(Sensor, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟传感器不存在")
    return sensor


def restart_backend_mqtt_client() -> None:
    mqtt_client.stop()
    if settings.mqtt_enabled:
        mqtt_client.start()
    simulator_manager.restart_client()


def ensure_sensor_code_unique(db: Session, sensor_code: str, exclude_id: int | None = None) -> None:
    query = db.query(Sensor).filter(Sensor.sensor_code == sensor_code)
    if exclude_id is not None:
        query = query.filter(Sensor.id != exclude_id)
    if query.first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="传感器编码已存在")


@router.get("/config", response_model=SimulatorConfigRead)
def get_simulator_config(
    _current_user: object = Depends(require_admin),
) -> dict:
    return simulator_manager.get_config_snapshot()


@router.put("/config", response_model=SimulatorConfigRead)
def update_simulator_config(
    payload: SimulatorConfigUpdate,
    _current_user: object = Depends(require_admin),
) -> dict:
    config = simulator_manager.update_config(
        enabled=payload.enabled,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        password=payload.password,
    )
    restart_backend_mqtt_client()
    return config


@router.get("/sensors", response_model=list[SimulatorSensorRead])
def get_simulator_sensors(
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> list[dict]:
    return sync_sensors_snapshot(db)


@router.post("/sensors/register", response_model=SimulatorSensorRead, status_code=status.HTTP_201_CREATED)
def register_simulator_sensor(
    payload: SimulatorSensorCreate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    ensure_sensor_code_unique(db, payload.sensor_code)

    sensor = Sensor(
        sensor_code=payload.sensor_code,
        sensor_name=payload.sensor_name,
        location=payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=payload.status,
        online=payload.online,
        base_light=payload.base_light,
        variance=payload.variance,
        voltage_base=payload.voltage_base,
        telemetry_interval_seconds=payload.telemetry_interval_seconds,
        status_every=payload.status_every,
    )
    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return simulator_manager.update_sensor_settings(
        sensor,
        bound_device=build_bound_device_map(db).get(sensor.id),
        running=payload.auto_start,
        base_light=payload.base_light,
        variance=payload.variance,
        voltage_base=payload.voltage_base,
        telemetry_interval_seconds=payload.telemetry_interval_seconds,
        status_every=payload.status_every,
        online=payload.online,
    )


@router.put("/sensors/{sensor_id}", response_model=SimulatorSensorRead)
def update_simulator_sensor(
    sensor_id: int,
    payload: SimulatorSensorUpdate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    sensor = get_sensor_or_404(db, sensor_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field in ("sensor_name", "location", "latitude", "longitude", "status"):
        if field in update_data:
            setattr(sensor, field, update_data[field])

    if "base_light" in update_data:
        sensor.base_light = update_data["base_light"]
    if "variance" in update_data:
        sensor.variance = update_data["variance"]
    if "voltage_base" in update_data:
        sensor.voltage_base = update_data["voltage_base"]
    if "telemetry_interval_seconds" in update_data:
        sensor.telemetry_interval_seconds = update_data["telemetry_interval_seconds"]
    if "status_every" in update_data:
        sensor.status_every = update_data["status_every"]
    if "online" in update_data:
        sensor.online = update_data["online"]

    if "online" in update_data and not update_data["online"]:
        sync_sensor_connection_state(db, sensor, online=False)
    elif "running" in update_data and update_data["running"] is False:
        sync_sensor_connection_state(db, sensor, online=False)

    db.commit()
    db.refresh(sensor)

    return simulator_manager.update_sensor_settings(
        sensor,
        bound_device=build_bound_device_map(db).get(sensor.id),
        running=update_data.get("running"),
        base_light=update_data.get("base_light"),
        variance=update_data.get("variance"),
        voltage_base=update_data.get("voltage_base"),
        telemetry_interval_seconds=update_data.get("telemetry_interval_seconds"),
        status_every=update_data.get("status_every"),
        online=update_data.get("online"),
    )


@router.post("/sensors/{sensor_id}/start", response_model=SimulatorSensorRead)
def start_simulator_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    get_sensor_or_404(db, sensor_id)
    sync_sensors_snapshot(db)
    state = simulator_manager.set_running(sensor_id, True)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟传感器不存在")
    return state


@router.post("/sensors/{sensor_id}/stop", response_model=SimulatorSensorRead)
def stop_simulator_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    sensor = get_sensor_or_404(db, sensor_id)
    sync_sensor_connection_state(db, sensor, online=False)
    db.commit()
    sync_sensors_snapshot(db)
    state = simulator_manager.set_running(sensor_id, False)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟传感器不存在")
    return state


@router.delete("/sensors/{sensor_id}")
def delete_simulator_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict[str, str]:
    sensor = get_sensor_or_404(db, sensor_id)
    bound_device = db.query(Device).filter(Device.sensor_id == sensor_id).first()
    if bound_device is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"传感器已绑定路灯 {bound_device.device_code}，请先解绑",
        )

    simulator_manager.remove_sensor(sensor_id)
    db.delete(sensor)
    db.commit()
    return {"message": "删除成功"}


@router.get("/logs", response_model=list[SimulatorLogRead])
def get_simulator_logs(
    limit: int = Query(default=120, ge=1, le=400),
    level: str | None = Query(default=None),
    _current_user: object = Depends(require_admin),
) -> list[dict]:
    return simulator_manager.get_logs(limit=limit, level=level)


@router.delete("/logs")
def clear_simulator_logs(
    _current_user: object = Depends(require_admin),
) -> dict[str, str]:
    simulator_manager.clear_logs()
    return {"message": "日志已清空"}
