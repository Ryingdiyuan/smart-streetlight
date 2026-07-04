from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.alarm_log import AlarmLog
from app.models.control_log import ControlLog
from app.models.device import Device
from app.models.light_data import LightData
from app.models.threshold_config import ThresholdConfig


class AgentContextError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def serialize_device(device: Device) -> dict[str, Any]:
    return {
        "id": device.id,
        "device_code": device.device_code,
        "device_name": device.device_name,
        "location": device.location,
        "status": device.status,
        "last_heartbeat_at": serialize_datetime(device.last_heartbeat_at),
    }


def serialize_light_data(light_data: LightData) -> dict[str, Any]:
    return {
        "id": light_data.id,
        "device_id": light_data.device_id,
        "light_intensity": light_data.light_intensity,
        "lamp_status": light_data.lamp_status,
        "voltage": light_data.voltage,
        "reported_at": serialize_datetime(light_data.reported_at),
        "created_at": serialize_datetime(light_data.created_at),
    }


def serialize_threshold_config(config: ThresholdConfig | None) -> dict[str, Any] | None:
    if config is None:
        return None
    return {
        "id": config.id,
        "device_id": config.device_id,
        "low_threshold": config.low_threshold,
        "high_threshold": config.high_threshold,
        "enabled": config.enabled,
        "updated_at": serialize_datetime(config.updated_at),
    }


def serialize_control_log(control_log: ControlLog) -> dict[str, Any]:
    return {
        "id": control_log.id,
        "device_id": control_log.device_id,
        "command": control_log.command,
        "source": control_log.source,
        "result": control_log.result,
        "request_payload": control_log.request_payload,
        "reply_payload": control_log.reply_payload,
        "created_at": serialize_datetime(control_log.created_at),
    }


def serialize_alarm_log(alarm_log: AlarmLog) -> dict[str, Any]:
    return {
        "id": alarm_log.id,
        "device_id": alarm_log.device_id,
        "alarm_type": alarm_log.alarm_type,
        "alarm_level": alarm_log.alarm_level,
        "alarm_content": alarm_log.alarm_content,
        "handled": alarm_log.handled,
        "handled_at": serialize_datetime(alarm_log.handled_at),
        "created_at": serialize_datetime(alarm_log.created_at),
    }


def get_device_for_agent(
    db: Session,
    device_id: int | None = None,
    device_code: str | None = None,
) -> Device | None:
    if device_id is not None:
        device = db.get(Device, device_id)
        if device is None:
            raise AgentContextError(404, "设备不存在")
        if device_code and device.device_code != device_code:
            raise AgentContextError(400, "device_id 与 device_code 不匹配")
        return device

    if device_code:
        device = db.query(Device).filter(Device.device_code == device_code).first()
        if device is None:
            raise AgentContextError(404, "设备不存在")
        return device

    return None


def build_device_context(db: Session, device: Device) -> dict[str, Any]:
    latest_light = (
        db.query(LightData)
        .filter(LightData.device_id == device.id)
        .order_by(LightData.reported_at.desc(), LightData.id.desc())
        .first()
    )
    light_history = (
        db.query(LightData)
        .filter(LightData.device_id == device.id)
        .order_by(LightData.reported_at.desc(), LightData.id.desc())
        .limit(5)
        .all()
    )
    threshold_config = (
        db.query(ThresholdConfig)
        .filter(ThresholdConfig.device_id == device.id)
        .first()
    )
    control_logs = (
        db.query(ControlLog)
        .filter(ControlLog.device_id == device.id)
        .order_by(ControlLog.created_at.desc(), ControlLog.id.desc())
        .limit(5)
        .all()
    )
    alarm_logs = (
        db.query(AlarmLog)
        .filter(AlarmLog.device_id == device.id)
        .order_by(AlarmLog.created_at.desc(), AlarmLog.id.desc())
        .limit(5)
        .all()
    )
    unhandled_alarm_count = (
        db.query(AlarmLog)
        .filter(
            AlarmLog.device_id == device.id,
            AlarmLog.handled.is_(False),
        )
        .count()
    )

    return {
        "scope": "device",
        "device": serialize_device(device),
        "latest_light": serialize_light_data(latest_light) if latest_light else None,
        "light_history": [serialize_light_data(item) for item in light_history],
        "threshold_config": serialize_threshold_config(threshold_config),
        "control_logs": [serialize_control_log(item) for item in control_logs],
        "alarm_logs": [serialize_alarm_log(item) for item in alarm_logs],
        "unhandled_alarm_count": unhandled_alarm_count,
        "summary": {
            "has_device": True,
            "latest_light_found": latest_light is not None,
            "alarm_count": len(alarm_logs),
            "control_log_count": len(control_logs),
            "unhandled_alarm_count": unhandled_alarm_count,
        },
    }


def build_system_context(db: Session) -> dict[str, Any]:
    device_count = db.query(Device).count()
    online_count = db.query(Device).filter(Device.status == "online").count()
    offline_count = db.query(Device).filter(Device.status == "offline").count()
    unhandled_alarm_count = db.query(AlarmLog).filter(AlarmLog.handled.is_(False)).count()
    recent_alarms = (
        db.query(AlarmLog)
        .order_by(AlarmLog.created_at.desc(), AlarmLog.id.desc())
        .limit(5)
        .all()
    )
    recent_control_logs = (
        db.query(ControlLog)
        .order_by(ControlLog.created_at.desc(), ControlLog.id.desc())
        .limit(5)
        .all()
    )

    return {
        "scope": "system",
        "device_stats": {
            "device_count": device_count,
            "online_count": online_count,
            "offline_count": offline_count,
        },
        "unhandled_alarm_count": unhandled_alarm_count,
        "recent_alarms": [serialize_alarm_log(item) for item in recent_alarms],
        "recent_control_logs": [serialize_control_log(item) for item in recent_control_logs],
        "summary": {
            "has_device": False,
            "latest_light_found": False,
            "alarm_count": len(recent_alarms),
            "control_log_count": len(recent_control_logs),
            "unhandled_alarm_count": unhandled_alarm_count,
            "device_count": device_count,
            "online_count": online_count,
            "offline_count": offline_count,
        },
    }


def build_agent_context(
    db: Session,
    device_id: int | None = None,
    device_code: str | None = None,
) -> dict[str, Any]:
    device = get_device_for_agent(db, device_id=device_id, device_code=device_code)
    if device is not None:
        return build_device_context(db, device)
    return build_system_context(db)
