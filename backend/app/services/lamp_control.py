import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.control_log import ControlLog
from app.models.device import Device
from app.models.sensor import Sensor

ALLOWED_COMMANDS = {"TURN_ON", "TURN_OFF", "SET_BRIGHTNESS"}


def build_command_payload(
    *,
    command: str,
    source: str,
    brightness: int | None = None,
) -> dict:
    if command not in ALLOWED_COMMANDS:
        raise ValueError("unsupported command")

    payload = {
        "command": command,
        "source": source,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if command == "SET_BRIGHTNESS" and brightness is not None:
        payload["brightness"] = brightness

    return payload


def resolve_command_topic(db: Session, device: Device) -> str:
    if device.sensor_id is not None:
        sensor = db.get(Sensor, device.sensor_id)
        if sensor is not None:
            return f"streetlight/{sensor.sensor_code}/command"
    return f"streetlight/{device.device_code}/command"


def apply_lamp_command(
    db: Session,
    device: Device,
    *,
    command: str,
    source: str,
    brightness: int | None = None,
) -> ControlLog:
    payload = build_command_payload(command=command, source=source, brightness=brightness)

    if not settings.mqtt_enabled:
        result = "skipped"
    else:
        from app.mqtt.client import mqtt_client

        topic = resolve_command_topic(db, device)
        published = mqtt_client.publish(topic, json.dumps(payload, ensure_ascii=False))
        result = "success" if published else "failed"

    if command == "TURN_ON":
        device.lamp_status = "ON"
    elif command == "TURN_OFF":
        device.lamp_status = "OFF"
    elif command == "SET_BRIGHTNESS":
        device.lamp_status = "ON" if (brightness or 0) > 0 else "OFF"

    control_log = ControlLog(
        device_id=device.id,
        command=command,
        source=source,
        result=result,
        request_payload=payload,
        reply_payload=None,
    )
    db.add(control_log)
    db.flush()
    return control_log
