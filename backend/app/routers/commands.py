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
from app.schemas.control_log import ControlCommandCreate, ControlLogRead

router = APIRouter(prefix="/devices/{device_id}/commands", tags=["commands"])

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


@router.post("", response_model=ControlLogRead, status_code=status.HTTP_201_CREATED)
def create_command(
    device_id: int,
    command_create: ControlCommandCreate,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_maintainer_or_admin),
) -> ControlLog:
    device = get_device_or_404(db, device_id)
    payload = build_command_payload(command_create)

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
    db.commit()
    db.refresh(control_log)
    return control_log


@router.get("", response_model=list[ControlLogRead])
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
