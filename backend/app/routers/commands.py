import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_maintainer_or_admin, require_user_or_above
from app.models.control_log import ControlLog
from app.models.device import Device
from app.mqtt.client import mqtt_client
from app.schemas.control_log import (
    BatchControlCommandCreate,
    BatchControlLogItemRead,
    BatchControlLogRead,
    ControlCommandCreate,
    ControlLogRead,
)

router = APIRouter(prefix="/devices", tags=["commands"])

ALLOWED_COMMANDS = {"TURN_ON", "TURN_OFF", "SET_BRIGHTNESS"}


def get_device_or_404(db: Session, device_id: int) -> Device:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在",
        )
    return device


def build_command_payload(command_create: ControlCommandCreate) -> dict:
    command = command_create.command
    if command not in ALLOWED_COMMANDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的控制命令",
        )

    payload = {
        "command": command,
        "source": "manual",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if command == "SET_BRIGHTNESS":
        if command_create.brightness is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SET_BRIGHTNESS 必须传 brightness",
            )
        if not 0 <= command_create.brightness <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="brightness 必须在 0 到 100 之间",
            )
        payload["brightness"] = command_create.brightness

    return payload


def create_control_log(db: Session, device: Device, payload: dict) -> ControlLog:
    if not settings.mqtt_enabled:
        result = "skipped"
    else:
        topic = f"streetlight/{device.device_code}/command"
        published = mqtt_client.publish(topic, json.dumps(payload, ensure_ascii=False))
        result = "success" if published else "failed"

    control_log = ControlLog(
        device_id=device.id,
        command=payload["command"],
        source="manual",
        result=result,
        request_payload=payload,
        reply_payload=None,
    )
    db.add(control_log)
    db.flush()
    return control_log


@router.post("/{device_id}/commands", response_model=ControlLogRead, status_code=status.HTTP_201_CREATED)
def create_command(
    device_id: int,
    command_create: ControlCommandCreate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_maintainer_or_admin),
) -> ControlLog:
    device = get_device_or_404(db, device_id)
    payload = build_command_payload(command_create)
    control_log = create_control_log(db, device, payload)
    db.commit()
    db.refresh(control_log)
    return control_log


@router.post("/commands/batch", response_model=BatchControlLogRead, status_code=status.HTTP_201_CREATED)
def create_batch_command(
    command_create: BatchControlCommandCreate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_maintainer_or_admin),
) -> BatchControlLogRead:
    device_ids = list(dict.fromkeys(command_create.device_ids))
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    device_map = {device.id: device for device in devices}
    missing_ids = [device_id for device_id in device_ids if device_id not in device_map]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"以下设备不存在：{', '.join(map(str, missing_ids))}",
        )

    payload = build_command_payload(command_create)
    results: list[BatchControlLogItemRead] = []
    success_count = 0
    failed_count = 0
    skipped_count = 0

    for device_id in device_ids:
        device = device_map[device_id]
        control_log = create_control_log(db, device, dict(payload))
        if control_log.result == "success":
            success_count += 1
        elif control_log.result == "failed":
            failed_count += 1
        else:
            skipped_count += 1

        results.append(
            BatchControlLogItemRead(
                device_id=device.id,
                device_code=device.device_code,
                result=control_log.result,
                log_id=control_log.id,
                created_at=control_log.created_at,
            )
        )

    db.commit()
    return BatchControlLogRead(
        command=payload["command"],
        total=len(device_ids),
        success_count=success_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        results=results,
    )


@router.get("/{device_id}/commands", response_model=list[ControlLogRead])
def list_commands(
    device_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
) -> list[ControlLog]:
    get_device_or_404(db, device_id)
    return (
        db.query(ControlLog)
        .filter(ControlLog.device_id == device_id)
        .order_by(ControlLog.created_at.desc(), ControlLog.id.desc())
        .limit(limit)
        .all()
    )
