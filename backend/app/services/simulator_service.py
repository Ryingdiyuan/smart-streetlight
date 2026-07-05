import json
import os
import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.models.device import Device


DEFAULT_DEVICE_PROFILE = {
    "base_light": 120,
    "variance": 35,
    "voltage_base": 220.5,
    "telemetry_interval_seconds": 5,
    "status_every": 1,
}


def format_time(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clamp(value: float, minimum: int, maximum: int) -> int:
    return int(max(minimum, min(maximum, round(value))))


@dataclass
class SimulatorLogEntry:
    created_at: datetime
    level: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "created_at": format_time(self.created_at) or "",
            "level": self.level,
            "message": self.message,
        }


@dataclass
class SimulatorDeviceState:
    device_id: int
    device_code: str
    device_name: str
    location: str | None
    running: bool = False
    lamp_status: str = "off"
    brightness: int = 0
    online: bool = True
    base_light: int = 120
    variance: int = 35
    voltage_base: float = 220.5
    telemetry_interval_seconds: int = 5
    status_every: int = 1
    publish_count: int = 0
    current_light_intensity: int = 0
    last_telemetry_at: datetime | None = None
    last_status_at: datetime | None = None
    last_command_at: datetime | None = None
    last_command: str | None = None
    next_publish_monotonic: float = 0.0

    def apply_defaults(self) -> None:
        self.base_light = self.base_light or int(DEFAULT_DEVICE_PROFILE["base_light"])
        self.variance = self.variance or int(DEFAULT_DEVICE_PROFILE["variance"])
        self.voltage_base = self.voltage_base or float(DEFAULT_DEVICE_PROFILE["voltage_base"])
        self.telemetry_interval_seconds = max(1, int(self.telemetry_interval_seconds or 5))
        self.status_every = max(1, int(self.status_every or 1))

    def build_status_payload(self) -> dict[str, Any]:
        return {
            "deviceId": self.device_code,
            "online": self.online,
            "lampStatus": self.lamp_status,
            "timestamp": now_text(),
        }

    def build_telemetry_payload(self) -> dict[str, Any]:
        ambient = self.base_light + random.randint(-self.variance, self.variance)
        lamp_boost = 0
        if self.lamp_status == "on":
            lamp_boost = max(30, int(self.brightness * 1.6))

        self.current_light_intensity = clamp(ambient + lamp_boost, 0, 1000)
        voltage = round(self.voltage_base + random.uniform(-1.2, 1.2), 1)
        return {
            "deviceId": self.device_code,
            "lightIntensity": self.current_light_intensity,
            "lampStatus": self.lamp_status,
            "voltage": voltage,
            "timestamp": now_text(),
        }

    def apply_command(self, payload: dict[str, Any]) -> None:
        command = str(payload.get("command", "")).upper()
        if command == "TURN_ON":
            self.lamp_status = "on"
            self.brightness = max(self.brightness, 80)
        elif command == "TURN_OFF":
            self.lamp_status = "off"
            self.brightness = 0
        elif command == "SET_BRIGHTNESS":
            raw_value = payload.get("brightness", 0)
            self.brightness = clamp(float(raw_value), 0, 100)
            self.lamp_status = "on" if self.brightness > 0 else "off"

        self.last_command = command or None
        self.last_command_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_code": self.device_code,
            "device_name": self.device_name,
            "location": self.location,
            "running": self.running,
            "online": self.online,
            "lamp_status": self.lamp_status,
            "brightness": self.brightness,
            "base_light": self.base_light,
            "variance": self.variance,
            "voltage_base": self.voltage_base,
            "telemetry_interval_seconds": self.telemetry_interval_seconds,
            "status_every": self.status_every,
            "publish_count": self.publish_count,
            "current_light_intensity": self.current_light_intensity,
            "last_telemetry_at": format_time(self.last_telemetry_at),
            "last_status_at": format_time(self.last_status_at),
            "last_command_at": format_time(self.last_command_at),
            "last_command": self.last_command,
        }


class SimulatorManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._devices: dict[int, SimulatorDeviceState] = {}
        self._logs: deque[SimulatorLogEntry] = deque(maxlen=400)
        self._stop_event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._client: mqtt.Client | None = None
        self._started = False
        self._connected = False

    def start(self) -> None:
        if self._started:
            return

        self._started = True
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._publish_loop,
            name="simulator-publisher",
            daemon=True,
        )
        self._worker_thread.start()
        self._connect_client_if_needed()
        self.append_log("INFO", "模拟器服务已启动")

    def stop(self) -> None:
        self._stop_event.set()
        self._disconnect_client()
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=3)
            self._worker_thread = None
        self._started = False
        self.append_log("INFO", "模拟器服务已停止")

    def append_log(self, level: str, message: str) -> None:
        with self._lock:
            self._logs.appendleft(
                SimulatorLogEntry(
                    created_at=datetime.now(),
                    level=level,
                    message=message,
                )
            )

    def get_logs(self, limit: int = 100, level: str | None = None) -> list[dict[str, str]]:
        with self._lock:
            items = list(self._logs)
            if level:
                normalized = level.upper()
                items = [item for item in items if item.level.upper() == normalized]
            return [item.to_dict() for item in items[:limit]]

    def clear_logs(self) -> None:
        with self._lock:
            self._logs.clear()
            self._logs.appendleft(
                SimulatorLogEntry(
                    created_at=datetime.now(),
                    level="INFO",
                    message="已清空模拟器运行日志",
                )
            )

    def get_config_snapshot(self) -> dict[str, Any]:
        return {
            "enabled": settings.mqtt_enabled,
            "host": settings.mqtt_host,
            "port": settings.mqtt_port,
            "username": settings.mqtt_username or "",
            "password": settings.mqtt_password or "",
            "client_id": f"{settings.mqtt_client_id}-simulator",
            "connected": self._connected,
        }

    def update_config(
        self,
        *,
        enabled: bool,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
    ) -> dict[str, Any]:
        settings.mqtt_enabled = enabled
        settings.mqtt_host = host
        settings.mqtt_port = port
        settings.mqtt_username = username or None
        settings.mqtt_password = password or None

        self.append_log(
            "INFO",
            f"已更新模拟器 MQTT 配置 {host}:{port} enabled={enabled}",
        )
        self.restart_client()
        return self.get_config_snapshot()

    def restart_client(self) -> None:
        self._disconnect_client()
        self._connect_client_if_needed()

    def sync_devices(self, devices: list[Device]) -> list[dict[str, Any]]:
        with self._lock:
            valid_ids = {device.id for device in devices}

            for device in devices:
                state = self._devices.get(device.id)
                if state is None:
                    state = SimulatorDeviceState(
                        device_id=device.id,
                        device_code=device.device_code,
                        device_name=device.device_name,
                        location=device.location,
                    )
                    state.apply_defaults()
                    self._devices[device.id] = state
                else:
                    state.device_code = device.device_code
                    state.device_name = device.device_name
                    state.location = device.location
                    state.apply_defaults()

            removed_ids = [item_id for item_id in self._devices if item_id not in valid_ids]
            for item_id in removed_ids:
                self._devices.pop(item_id, None)

            return [
                self._devices[device.id].to_dict()
                for device in sorted(devices, key=lambda item: item.id)
                if device.id in self._devices
            ]

    def sync_device(self, device: Device) -> dict[str, Any]:
        with self._lock:
            state = self._devices.get(device.id)
            if state is None:
                state = SimulatorDeviceState(
                    device_id=device.id,
                    device_code=device.device_code,
                    device_name=device.device_name,
                    location=device.location,
                )
                self._devices[device.id] = state
            else:
                state.device_code = device.device_code
                state.device_name = device.device_name
                state.location = device.location

            state.apply_defaults()
            return state.to_dict()

    def update_device_settings(
        self,
        device: Device,
        *,
        running: bool | None = None,
        base_light: int | None = None,
        variance: int | None = None,
        voltage_base: float | None = None,
        telemetry_interval_seconds: int | None = None,
        status_every: int | None = None,
        online: bool | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            state = self._devices.get(device.id)
            if state is None:
                state = SimulatorDeviceState(
                    device_id=device.id,
                    device_code=device.device_code,
                    device_name=device.device_name,
                    location=device.location,
                )
                self._devices[device.id] = state

            state.device_code = device.device_code
            state.device_name = device.device_name
            state.location = device.location

            if running is not None:
                state.running = running
                state.next_publish_monotonic = 0
            if base_light is not None:
                state.base_light = base_light
            if variance is not None:
                state.variance = variance
            if voltage_base is not None:
                state.voltage_base = voltage_base
            if telemetry_interval_seconds is not None:
                state.telemetry_interval_seconds = max(1, telemetry_interval_seconds)
            if status_every is not None:
                state.status_every = max(1, status_every)
            if online is not None:
                state.online = online

            state.apply_defaults()
            return state.to_dict()

    def set_running(self, device_id: int, running: bool) -> dict[str, Any] | None:
        with self._lock:
            state = self._devices.get(device_id)
            if state is None:
                return None
            state.running = running
            state.next_publish_monotonic = 0
            message = "启动" if running else "停止"
            self._logs.appendleft(
                SimulatorLogEntry(
                    created_at=datetime.now(),
                    level="INFO",
                    message=f"{message}模拟设备 {state.device_code}",
                )
            )
            return state.to_dict()

    def remove_device(self, device_id: int) -> None:
        with self._lock:
            removed = self._devices.pop(device_id, None)
            if removed is not None:
                self._logs.appendleft(
                    SimulatorLogEntry(
                        created_at=datetime.now(),
                        level="WARN",
                        message=f"移除模拟设备 {removed.device_code}",
                    )
                )

    def _build_client(self) -> mqtt.Client:
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"{settings.mqtt_client_id}-simulator-{os.getpid()}",
        )
        if settings.mqtt_username:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        return client

    def _connect_client_if_needed(self) -> None:
        if not settings.mqtt_enabled:
            self._connected = False
            self.append_log("WARN", "MQTT 已禁用，模拟器不会发送数据")
            return

        try:
            self._client = self._build_client()
            self._client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            self._client.loop_start()
            self.append_log(
                "INFO",
                f"模拟器连接 MQTT Broker {settings.mqtt_host}:{settings.mqtt_port}",
            )
        except OSError as error:
            self._connected = False
            self._client = None
            self.append_log("ERROR", f"模拟器连接 MQTT 失败：{error}")

    def _disconnect_client(self) -> None:
        if self._client is None:
            self._connected = False
            return

        try:
            self._client.loop_stop()
            self._client.disconnect()
        finally:
            self._client = None
            self._connected = False

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        is_failure = getattr(reason_code, "is_failure", False)
        if callable(is_failure):
            is_failure = is_failure()
        if is_failure:
            self._connected = False
            self.append_log("ERROR", f"模拟器连接 MQTT 失败：{reason_code}")
            return

        self._connected = True
        client.subscribe("streetlight/+/command")
        self.append_log("INFO", "模拟器已订阅 streetlight/+/command")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        self._connected = False
        self.append_log("WARN", f"模拟器 MQTT 断开：{reason_code}")

    def _on_message(self, client, userdata, message) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.append_log("WARN", f"收到非法命令消息 topic={message.topic}")
            return

        topic_parts = message.topic.split("/")
        if len(topic_parts) < 3:
            return

        device_code = topic_parts[1]
        device_id: int | None = None
        with self._lock:
            state = next(
                (item for item in self._devices.values() if item.device_code == device_code),
                None,
            )
            if state is None:
                return
            state.apply_command(payload)
            device_id = state.device_id
            self._logs.appendleft(
                SimulatorLogEntry(
                    created_at=datetime.now(),
                    level="INFO",
                    message=(
                        f"设备 {device_code} 收到命令 {payload.get('command')}，"
                        f"lamp={state.lamp_status} brightness={state.brightness}"
                    ),
                )
            )
        if device_id is not None:
            self._publish_device_snapshot(device_id)

    def _publish_device_snapshot(self, device_id: int) -> None:
        with self._lock:
            state = self._devices.get(device_id)
            if state is None:
                return

            status_payload = state.build_status_payload()
            telemetry_payload = state.build_telemetry_payload()
            state.publish_count += 1
            state.next_publish_monotonic = time.monotonic() + state.telemetry_interval_seconds
            device_code = state.device_code

        if self._publish_json(f"streetlight/{device_code}/status", status_payload):
            with self._lock:
                if device_id in self._devices:
                    self._devices[device_id].last_status_at = datetime.now()

        if self._publish_json(f"streetlight/{device_code}/telemetry", telemetry_payload):
            with self._lock:
                if device_id in self._devices:
                    self._devices[device_id].last_telemetry_at = datetime.now()

        self.append_log("INFO", f"设备 {device_code} 已根据控制命令立即上报最新状态")

    def _publish_json(self, topic: str, payload: dict[str, Any]) -> bool:
        if not settings.mqtt_enabled:
            return False
        if self._client is None or not self._connected:
            self.append_log("WARN", f"模拟器未连接 MQTT，跳过发送 {topic}")
            return False

        text = json.dumps(payload, ensure_ascii=False)
        try:
            result = self._client.publish(topic, text, qos=0)
        except Exception as error:  # noqa: BLE001
            self.append_log("ERROR", f"发送 MQTT 消息失败 topic={topic} error={error}")
            return False

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            self.append_log("ERROR", f"发送 MQTT 消息失败 topic={topic} rc={result.rc}")
            return False

        self.append_log("INFO", f"发送 {topic} {text}")
        return True

    def _publish_loop(self) -> None:
        while not self._stop_event.wait(1):
            now_monotonic = time.monotonic()
            due_ids: list[int] = []
            with self._lock:
                for device_id, state in self._devices.items():
                    if not state.running:
                        continue
                    if state.next_publish_monotonic and now_monotonic < state.next_publish_monotonic:
                        continue
                    due_ids.append(device_id)

            for device_id in due_ids:
                with self._lock:
                    state = self._devices.get(device_id)
                    if state is None or not state.running:
                        continue

                    next_count = state.publish_count + 1
                    need_status = next_count == 1 or next_count % state.status_every == 0
                    status_payload = state.build_status_payload() if need_status else None
                    telemetry_payload = state.build_telemetry_payload()
                    state.publish_count = next_count
                    state.next_publish_monotonic = now_monotonic + state.telemetry_interval_seconds

                if status_payload is not None and self._publish_json(
                    f"streetlight/{state.device_code}/status",
                    status_payload,
                ):
                    with self._lock:
                        if device_id in self._devices:
                            self._devices[device_id].last_status_at = datetime.now()

                if self._publish_json(
                    f"streetlight/{state.device_code}/telemetry",
                    telemetry_payload,
                ):
                    with self._lock:
                        if device_id in self._devices:
                            self._devices[device_id].last_telemetry_at = datetime.now()


simulator_manager = SimulatorManager()
