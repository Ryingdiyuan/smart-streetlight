from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_admin
from app.models.alarm_log import AlarmLog
from app.models.control_log import ControlLog
from app.models.device import Device
from app.models.light_data import LightData
from app.models.threshold_config import ThresholdConfig
from app.mqtt.client import mqtt_client
from app.routers.devices import ensure_device_code_unique, get_device_or_404
from app.schemas.simulator import (
    SimulatorConfigRead,
    SimulatorConfigUpdate,
    SimulatorDeviceCreate,
    SimulatorDeviceRead,
    SimulatorDeviceUpdate,
    SimulatorLogRead,
)
from app.services.simulator_service import simulator_manager

router = APIRouter(prefix="/simulator", tags=["simulator"])


def list_all_devices(db: Session) -> list[Device]:
    return db.query(Device).order_by(Device.id.asc()).all()


def sync_devices_snapshot(db: Session) -> list[dict]:
    return simulator_manager.sync_devices(list_all_devices(db))


def get_state_or_404(db: Session, device_id: int) -> tuple[Device, dict]:
    device = get_device_or_404(db, device_id)
    return device, simulator_manager.sync_device(device)


def restart_backend_mqtt_client() -> None:
    mqtt_client.stop()
    if settings.mqtt_enabled:
        mqtt_client.start()
    simulator_manager.restart_client()


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


@router.get("/devices", response_model=list[SimulatorDeviceRead])
def get_simulator_devices(
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> list[dict]:
    return sync_devices_snapshot(db)


@router.post("/devices", response_model=SimulatorDeviceRead, status_code=status.HTTP_201_CREATED)
def create_simulator_device(
    payload: SimulatorDeviceCreate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    ensure_device_code_unique(db, payload.device_code)

    device = Device(
        device_code=payload.device_code,
        device_name=payload.device_name,
        location=payload.location,
        status=payload.status,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    simulator_manager.sync_device(device)
    return simulator_manager.update_device_settings(
        device,
        running=payload.auto_start,
        base_light=payload.base_light,
        variance=payload.variance,
        voltage_base=payload.voltage_base,
        telemetry_interval_seconds=payload.telemetry_interval_seconds,
        status_every=payload.status_every,
        online=payload.online,
    )


@router.put("/devices/{device_id}", response_model=SimulatorDeviceRead)
def update_simulator_device(
    device_id: int,
    payload: SimulatorDeviceUpdate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    device = get_device_or_404(db, device_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field in ("device_name", "location", "status"):
        if field in update_data:
            setattr(device, field, update_data[field])

    db.commit()
    db.refresh(device)

    simulator_manager.sync_device(device)
    return simulator_manager.update_device_settings(
        device,
        running=update_data.get("running"),
        base_light=update_data.get("base_light"),
        variance=update_data.get("variance"),
        voltage_base=update_data.get("voltage_base"),
        telemetry_interval_seconds=update_data.get("telemetry_interval_seconds"),
        status_every=update_data.get("status_every"),
        online=update_data.get("online"),
    )


@router.post("/devices/{device_id}/start", response_model=SimulatorDeviceRead)
def start_simulator_device(
    device_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    get_device_or_404(db, device_id)
    sync_devices_snapshot(db)
    state = simulator_manager.set_running(device_id, True)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟设备不存在")
    return state


@router.post("/devices/{device_id}/stop", response_model=SimulatorDeviceRead)
def stop_simulator_device(
    device_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict:
    get_device_or_404(db, device_id)
    sync_devices_snapshot(db)
    state = simulator_manager.set_running(device_id, False)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟设备不存在")
    return state


@router.delete("/devices/{device_id}")
def delete_simulator_device(
    device_id: int,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_admin),
) -> dict[str, str]:
    get_device_or_404(db, device_id)
    simulator_manager.remove_device(device_id)
    try:
        # 删除关联数据，避免外键约束冲突
        db.query(LightData).filter(LightData.device_id == device_id).delete()
        db.query(ThresholdConfig).filter(ThresholdConfig.device_id == device_id).delete()
        db.query(ControlLog).filter(ControlLog.device_id == device_id).delete()
        db.query(AlarmLog).filter(AlarmLog.device_id == device_id).delete()
        db.query(Device).filter(Device.id == device_id).delete()
        db.commit()
    except Exception as error:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"删除设备失败：{error}",
        ) from error

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
