import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.device import Device
from app.models.light_data import LightData
from app.services.auto_control import evaluate_auto_control

logger = logging.getLogger(__name__)


def parse_reported_at(value: Any) -> datetime:
    if not value:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    for parser in (
        lambda item: datetime.fromisoformat(item),
        lambda item: datetime.strptime(item, "%Y-%m-%d %H:%M:%S"),
    ):
        try:
            return parser(text)
        except ValueError:
            continue

    logger.warning("Invalid telemetry timestamp %s, using current time", value)
    return datetime.utcnow()


def handle_telemetry_payload(payload: dict[str, Any], db: Session) -> None:
    device_code = payload.get("deviceId") or payload.get("device_code")
    if not device_code:
        logger.warning("Telemetry payload missing deviceId: %s", payload)
        return

    light_intensity = payload.get("lightIntensity")
    if light_intensity is None:
        logger.warning("Telemetry payload missing lightIntensity: %s", payload)
        return

    device = db.query(Device).filter(Device.device_code == device_code).first()
    if device is None:
        logger.warning("Telemetry device not registered: %s", device_code)
        return

    voltage = payload.get("voltage")
    light_data = LightData(
        device_id=device.id,
        light_intensity=int(light_intensity),
        lamp_status=payload.get("lampStatus") or "off",
        voltage=float(voltage) if voltage is not None else None,
        reported_at=parse_reported_at(payload.get("timestamp")),
    )
    db.add(light_data)
    db.commit()
    db.refresh(light_data)

    suggested_action = evaluate_auto_control(
        db,
        device.id,
        light_data.light_intensity,
    )
    logger.info(
        "Saved MQTT telemetry for device %s, suggested_action=%s",
        device_code,
        suggested_action,
    )


def handle_telemetry_message(topic: str, payload_bytes: bytes) -> None:
    try:
        payload_text = payload_bytes.decode("utf-8")
        payload = json.loads(payload_text)
    except UnicodeDecodeError:
        logger.warning("Telemetry payload is not valid UTF-8, topic=%s", topic)
        return
    except json.JSONDecodeError:
        logger.warning("Telemetry payload is not valid JSON, topic=%s", topic)
        return

    if not isinstance(payload, dict):
        logger.warning("Telemetry payload is not a JSON object, topic=%s", topic)
        return

    db = SessionLocal()
    try:
        handle_telemetry_payload(payload, db)
    except (TypeError, ValueError):
        db.rollback()
        logger.exception("Invalid telemetry payload, topic=%s payload=%s", topic, payload)
    except Exception:
        db.rollback()
        logger.exception("Failed to save MQTT telemetry, topic=%s", topic)
    finally:
        db.close()
