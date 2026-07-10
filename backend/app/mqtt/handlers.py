import json
import logging
from datetime import datetime
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.alarm_log import AlarmLog
from app.models.device import Device
from app.models.light_data import LightData
from app.models.sensor import Sensor
from app.services.auto_control import ACTION_TURN_OFF, ACTION_TURN_ON, evaluate_auto_control
from app.services.lamp_control import apply_lamp_command

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

    logger.warning("Invalid MQTT timestamp %s, using current time", value)
    return datetime.utcnow()


def parse_online_status(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "online", "on", "yes"}
    return bool(value)


def extract_sensor_code(payload: dict[str, Any]) -> str | None:
    for key in ("sensorId", "sensor_code", "sensorCode", "deviceId", "device_code"):
        value = payload.get(key)
        if value:
            return str(value).strip()
    return None


def get_sensor_by_payload(db: Session, payload: dict[str, Any]) -> Sensor | None:
    sensor_code = extract_sensor_code(payload)
    if not sensor_code:
        return None
    return db.query(Sensor).filter(Sensor.sensor_code == sensor_code).first()


def get_bound_device(db: Session, sensor_id: int) -> Device | None:
    return db.query(Device).filter(Device.sensor_id == sensor_id).first()


def handle_register_payload(payload: dict[str, Any], db: Session) -> None:
    sensor_code = extract_sensor_code(payload)
    if not sensor_code:
        logger.warning("Register payload missing sensor code: %s", payload)
        return

    sensor_name = payload.get("sensorName") or payload.get("sensor_name") or sensor_code
    sensor = db.query(Sensor).filter(Sensor.sensor_code == sensor_code).first()
    created = sensor is None

    if sensor is None:
        sensor = Sensor(
            sensor_code=sensor_code,
            sensor_name=str(sensor_name),
        )
        db.add(sensor)

    sensor.sensor_name = str(sensor_name)
    sensor.location = payload.get("location") or sensor.location
    sensor.latitude = payload.get("latitude", sensor.latitude)
    sensor.longitude = payload.get("longitude", sensor.longitude)
    sensor.status = "online" if parse_online_status(payload.get("online")) else "offline"
    sensor.last_heartbeat_at = parse_reported_at(payload.get("timestamp"))

    db.commit()
    db.refresh(sensor)
    logger.info("Sensor %s via register topic: %s", sensor.sensor_code, "created" if created else "updated")


def handle_telemetry_payload(payload: dict[str, Any], db: Session) -> None:
    sensor = get_sensor_by_payload(db, payload)
    sensor_code = extract_sensor_code(payload)
    if sensor is None:
        logger.warning("Telemetry sensor not registered: %s", sensor_code or payload)
        return

    light_intensity = payload.get("lightIntensity")
    if light_intensity is None:
        logger.warning("Telemetry payload missing lightIntensity: %s", payload)
        return

    sensor.status = "online"
    sensor.last_heartbeat_at = parse_reported_at(payload.get("timestamp"))
    bound_device = get_bound_device(db, sensor.id)
    if bound_device is None:
        db.commit()
        logger.info("Drop telemetry from unbound sensor %s", sensor.sensor_code)
        return

    voltage = payload.get("voltage")
    lamp_status = str(payload.get("lampStatus") or bound_device.lamp_status or "OFF").upper()

    light_data = LightData(
        device_id=bound_device.id,
        light_intensity=int(light_intensity),
        lamp_status=lamp_status.lower(),
        voltage=float(voltage) if voltage is not None else None,
        reported_at=parse_reported_at(payload.get("timestamp")),
    )
    db.add(light_data)

    bound_device.status = "online"
    bound_device.last_heartbeat_at = sensor.last_heartbeat_at
    bound_device.lamp_status = lamp_status

    suggested_action = evaluate_auto_control(db, bound_device.id, light_data.light_intensity)
    if bound_device.control_mode == "auto" and suggested_action in {ACTION_TURN_ON, ACTION_TURN_OFF}:
        desired_lamp_status = "ON" if suggested_action == ACTION_TURN_ON else "OFF"
        if bound_device.lamp_status != desired_lamp_status:
            apply_lamp_command(
                db,
                bound_device,
                command=suggested_action,
                source="auto",
            )

    db.commit()
    db.refresh(light_data)
    logger.info(
        "Saved telemetry for sensor %s bound to device %s",
        sensor.sensor_code,
        bound_device.device_code,
    )


def handle_status_payload(payload: dict[str, Any], db: Session) -> None:
    sensor = get_sensor_by_payload(db, payload)
    sensor_code = extract_sensor_code(payload)
    if sensor is None:
        logger.warning("Status sensor not registered: %s", sensor_code or payload)
        return

    is_online = parse_online_status(payload.get("online"))
    sensor.status = "online" if is_online else "offline"
    sensor.last_heartbeat_at = parse_reported_at(payload.get("timestamp"))

    bound_device = get_bound_device(db, sensor.id)
    if bound_device is not None:
        bound_device.status = sensor.status
        bound_device.last_heartbeat_at = sensor.last_heartbeat_at
        if payload.get("lampStatus"):
            bound_device.lamp_status = str(payload["lampStatus"]).upper()

        if is_online:
            (
                db.query(AlarmLog)
                .filter(
                    AlarmLog.device_id == bound_device.id,
                    AlarmLog.alarm_type == "offline",
                    AlarmLog.handled.is_(False),
                )
                .update(
                    {
                        AlarmLog.handled: True,
                        AlarmLog.handled_at: datetime.utcnow(),
                    },
                    synchronize_session=False,
                )
            )

    db.commit()
    logger.info("Updated status from sensor %s to %s", sensor.sensor_code, sensor.status)


def decode_payload(payload_bytes: bytes, topic: str, kind: str) -> dict[str, Any] | None:
    try:
        payload_text = payload_bytes.decode("utf-8")
        payload = json.loads(payload_text)
    except UnicodeDecodeError:
        logger.warning("%s payload is not valid UTF-8, topic=%s", kind, topic)
        return None
    except json.JSONDecodeError:
        logger.warning("%s payload is not valid JSON, topic=%s", kind, topic)
        return None

    if not isinstance(payload, dict):
        logger.warning("%s payload is not a JSON object, topic=%s", kind, topic)
        return None
    return payload


def process_message(
    topic: str,
    payload_bytes: bytes,
    *,
    kind: str,
    handler: Callable[[dict[str, Any], Session], None],
) -> None:
    payload = decode_payload(payload_bytes, topic, kind)
    if payload is None:
        return

    db = SessionLocal()
    try:
        handler(payload, db)
    except (TypeError, ValueError):
        db.rollback()
        logger.exception("Invalid %s payload, topic=%s payload=%s", kind, topic, payload)
    except Exception:
        db.rollback()
        logger.exception("Failed to process %s message, topic=%s", kind, topic)
    finally:
        db.close()


def handle_register_message(topic: str, payload_bytes: bytes) -> None:
    process_message(topic, payload_bytes, kind="register", handler=handle_register_payload)


def handle_telemetry_message(topic: str, payload_bytes: bytes) -> None:
    process_message(topic, payload_bytes, kind="telemetry", handler=handle_telemetry_payload)


def handle_status_message(topic: str, payload_bytes: bytes) -> None:
    process_message(topic, payload_bytes, kind="status", handler=handle_status_payload)
