import json
import os
import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.models.device import Device
from app.models.sensor import Sensor

DEFAULT_SENSOR_PROFILE = {
    "base_light": 120,
    "variance": 35,
    "voltage_base": 220.5,
    "telemetry_interval_seconds": 20,
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
class HeartbeatPublisher:
    online: bool = True
    status_every: int = 1
    last_status_at: datetime | None = None
    next_status_monotonic: float = 0.0

    def apply_defaults(self) -> None:
        self.status_every = max(1, int(self.status_every or DEFAULT_SENSOR_PROFILE["status_every"]))

    def reset_cycle(self) -> None:
        self.next_status_monotonic = 0.0

    def should_publish(self, now_monotonic: float) -> bool:
        return not self.next_status_monotonic or now_monotonic >= self.next_status_monotonic

    def schedule_next(self, now_monotonic: float) -> None:
        self.next_status_monotonic = now_monotonic + self.status_every

    def build_payload(self, sensor_code: str, lamp_status: str) -> dict[str, Any]:
        return {
            "sensorId": sensor_code,
            "online": self.online,
            "lampStatus": lamp_status,
            "timestamp": now_text(),
        }

    def mark_published(self, published_at: datetime) -> None:
        self.last_status_at = published_at


@dataclass
class TelemetryPublisher:
    base_light: int = 120
    variance: int = 35
    voltage_base: float = 220.5
    interval_seconds: int = 20
    publish_count: int = 0
    current_light_intensity: int = 0
    last_telemetry_at: datetime | None = None

    def apply_defaults(self) -> None:
        self.base_light = self.base_light or int(DEFAULT_SENSOR_PROFILE["base_light"])
        self.variance = self.variance or int(DEFAULT_SENSOR_PROFILE["variance"])
        self.voltage_base = self.voltage_base or float(DEFAULT_SENSOR_PROFILE["voltage_base"])
        self.interval_seconds = max(1, int(self.interval_seconds or DEFAULT_SENSOR_PROFILE["telemetry_interval_seconds"]))

    def build_payload(self, sensor_code: str, lamp_status: str, brightness: int) -> dict[str, Any]:
        ambient = self.base_light + random.randint(-self.variance, self.variance)
        lamp_boost = max(30, int(brightness * 1.6)) if lamp_status == "on" else 0
        self.current_light_intensity = clamp(ambient + lamp_boost, 0, 1000)
        voltage = round(self.voltage_base + random.uniform(-1.2, 1.2), 1)
        return {
            "sensorId": sensor_code,
            "lightIntensity": self.current_light_intensity,
            "lampStatus": lamp_status,
            "voltage": voltage,
            "timestamp": now_text(),
        }

    def mark_published(self, published_at: datetime) -> None:
        self.publish_count += 1
        self.last_telemetry_at = published_at


@dataclass
class SimulatorSensorState:
    sensor_id: int
    sensor_code: str
    sensor_name: str
    location: str | None
    running: bool = False
    lamp_status: str = "off"
    brightness: int = 0
    heartbeat: HeartbeatPublisher = field(default_factory=HeartbeatPublisher)
    telemetry: TelemetryPublisher = field(default_factory=TelemetryPublisher)
    last_command_at: datetime | None = None
    last_command: str | None = None
    system_status: str = "offline"
    bound_device_id: int | None = None
    bound_device_code: str | None = None
    bound_device_name: str | None = None
    control_mode: str | None = None
    next_publish_monotonic: float = 0.0

    @property
    def online(self) -> bool:
        return self.heartbeat.online

    @online.setter
    def online(self, value: bool) -> None:
        self.heartbeat.online = value

    @property
    def base_light(self) -> int:
        return self.telemetry.base_light

    @base_light.setter
    def base_light(self, value: int) -> None:
        self.telemetry.base_light = value

    @property
    def variance(self) -> int:
        return self.telemetry.variance

    @variance.setter
    def variance(self, value: int) -> None:
        self.telemetry.variance = value

    @property
    def voltage_base(self) -> float:
        return self.telemetry.voltage_base

    @voltage_base.setter
    def voltage_base(self, value: float) -> None:
        self.telemetry.voltage_base = value

    @property
    def telemetry_interval_seconds(self) -> int:
        return self.telemetry.interval_seconds

    @telemetry_interval_seconds.setter
    def telemetry_interval_seconds(self, value: int) -> None:
        self.telemetry.interval_seconds = value

    @property
    def status_every(self) -> int:
        return self.heartbeat.status_every

    @status_every.setter
    def status_every(self, value: int) -> None:
        self.heartbeat.status_every = value

    @property
    def publish_count(self) -> int:
        return self.telemetry.publish_count

    @property
    def current_light_intensity(self) -> int:
        return self.telemetry.current_light_intensity

    @property
    def last_telemetry_at(self) -> datetime | None:
        return self.telemetry.last_telemetry_at

    @property
    def last_status_at(self) -> datetime | None:
        return self.heartbeat.last_status_at

    def apply_defaults(self) -> None:
        self.telemetry.apply_defaults()
        self.heartbeat.apply_defaults()

    def reset_runtime_cycle(self) -> None:
        self.next_publish_monotonic = 0
        self.heartbeat.reset_cycle()

    def build_status_payload(self) -> dict[str, Any]:
        return self.heartbeat.build_payload(self.sensor_code, self.lamp_status)

    def build_telemetry_payload(self) -> dict[str, Any]:
        return self.telemetry.build_payload(self.sensor_code, self.lamp_status, self.brightness)

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
            "sensor_id": self.sensor_id,
            "sensor_code": self.sensor_code,
            "sensor_name": self.sensor_name,
            "location": self.location,
            "running": self.running,
            "online": self.online,
            "system_status": self.system_status,
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
            "bound_device_id": self.bound_device_id,
            "bound_device_code": self.bound_device_code,
            "bound_device_name": self.bound_device_name,
            "control_mode": self.control_mode,
        }


class SimulatorManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sensors: dict[int, SimulatorSensorState] = {}
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
        self.append_log("INFO", "传感器模拟器已启动")

    def stop(self) -> None:
        self._stop_event.set()
        self._disconnect_client()
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=3)
            self._worker_thread = None
        self._started = False
        self.append_log("INFO", "传感器模拟器已停止")

    def append_log(self, level: str, message: str) -> None:
        with self._lock:
            self._logs.appendleft(SimulatorLogEntry(created_at=datetime.now(), level=level, message=message))

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
                    message="已清空传感器模拟器日志",
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
        self.append_log("INFO", f"已更新模拟器 MQTT 配置 {host}:{port} enabled={enabled}")
        self.restart_client()
        return self.get_config_snapshot()

    def restart_client(self) -> None:
        self._disconnect_client()
        self._connect_client_if_needed()

    def sync_sensors(
        self,
        sensors: list[Sensor],
        bound_devices: dict[int, Device | None] | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            bound_devices = bound_devices or {}
            valid_ids = {sensor.id for sensor in sensors}

            for sensor in sensors:
                state = self._sensors.get(sensor.id)
                if state is None:
                    state = SimulatorSensorState(
                        sensor_id=sensor.id,
                        sensor_code=sensor.sensor_code,
                        sensor_name=sensor.sensor_name,
                        location=sensor.location,
                    )
                    self._sensors[sensor.id] = state

                self._hydrate_state(state, sensor, bound_devices.get(sensor.id))

            removed_ids = [sensor_id for sensor_id in self._sensors if sensor_id not in valid_ids]
            for sensor_id in removed_ids:
                self._sensors.pop(sensor_id, None)

            return [self._sensors[sensor.id].to_dict() for sensor in sorted(sensors, key=lambda item: item.id)]

    def sync_sensor(self, sensor: Sensor, bound_device: Device | None = None) -> dict[str, Any]:
        with self._lock:
            state = self._sensors.get(sensor.id)
            if state is None:
                state = SimulatorSensorState(
                    sensor_id=sensor.id,
                    sensor_code=sensor.sensor_code,
                    sensor_name=sensor.sensor_name,
                    location=sensor.location,
                )
                self._sensors[sensor.id] = state

            self._hydrate_state(state, sensor, bound_device)
            return state.to_dict()

    def update_sensor_settings(
        self,
        sensor: Sensor,
        *,
        bound_device: Device | None = None,
        running: bool | None = None,
        base_light: int | None = None,
        variance: int | None = None,
        voltage_base: float | None = None,
        telemetry_interval_seconds: int | None = None,
        status_every: int | None = None,
        online: bool | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            state = self._sensors.get(sensor.id)
            if state is None:
                state = SimulatorSensorState(
                    sensor_id=sensor.id,
                    sensor_code=sensor.sensor_code,
                    sensor_name=sensor.sensor_name,
                    location=sensor.location,
                )
                self._sensors[sensor.id] = state

            self._hydrate_state(state, sensor, bound_device)

            if running is not None:
                state.running = running
                state.reset_runtime_cycle()
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

    def set_running(self, sensor_id: int, running: bool) -> dict[str, Any] | None:
        with self._lock:
            state = self._sensors.get(sensor_id)
            if state is None:
                return None
            state.running = running
            state.reset_runtime_cycle()
            self._logs.appendleft(
                SimulatorLogEntry(
                    created_at=datetime.now(),
                    level="INFO",
                    message=f"传感器 {state.sensor_code} 已{'启动' if running else '停止'}模拟",
                )
            )
            return state.to_dict()

    def remove_sensor(self, sensor_id: int) -> None:
        with self._lock:
            state = self._sensors.pop(sensor_id, None)
            if state is not None:
                self._logs.appendleft(
                    SimulatorLogEntry(
                        created_at=datetime.now(),
                        level="INFO",
                        message=f"传感器 {state.sensor_code} 已从模拟器移除",
                    )
                )

    def _hydrate_state(
        self,
        state: SimulatorSensorState,
        sensor: Sensor,
        bound_device: Device | None,
    ) -> None:
        state.sensor_code = sensor.sensor_code
        state.sensor_name = sensor.sensor_name
        state.location = sensor.location
        state.system_status = sensor.status or "offline"
        state.online = sensor.online
        state.base_light = sensor.base_light
        state.variance = sensor.variance
        state.voltage_base = sensor.voltage_base
        state.telemetry_interval_seconds = sensor.telemetry_interval_seconds
        state.status_every = sensor.status_every
        state.bound_device_id = bound_device.id if bound_device else None
        state.bound_device_code = bound_device.device_code if bound_device else None
        state.bound_device_name = bound_device.device_name if bound_device else None
        state.control_mode = bound_device.control_mode if bound_device else None
        state.apply_defaults()

    def _connect_client_if_needed(self) -> None:
        if not settings.mqtt_enabled or self._client is not None:
            return

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"{settings.mqtt_client_id}-sim-{os.getpid()}")
        if settings.mqtt_username:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message

        try:
            client.connect(settings.mqtt_host, settings.mqtt_port)
            client.loop_start()
            self._client = client
            self.append_log("INFO", "传感器模拟器 MQTT 客户端已启动")
        except OSError:
            self.append_log("ERROR", "传感器模拟器连接 MQTT Broker 失败")

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

    def _publish(self, topic: str, payload: dict[str, Any]) -> bool:
        client = self._client
        if client is None or not self._connected:
            return False
        result = client.publish(topic, json.dumps(payload, ensure_ascii=False))
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def _publish_loop(self) -> None:
        while not self._stop_event.is_set():
            now_monotonic = time.monotonic()
            with self._lock:
                states = list(self._sensors.values())

            for state in states:
                if not state.running:
                    continue
                if not state.next_publish_monotonic or now_monotonic >= state.next_publish_monotonic:
                    if state.online:
                        telemetry_payload = state.build_telemetry_payload()
                        telemetry_ok = self._publish(
                            f"streetlight/{state.sensor_code}/telemetry",
                            telemetry_payload,
                        )
                        published_at = datetime.now()
                        state.telemetry.mark_published(published_at)
                        if telemetry_ok:
                            self.append_log(
                                "INFO",
                                f"传感器 {state.sensor_code} 已发送 telemetry light={state.current_light_intensity}",
                            )
                        else:
                            self.append_log("WARN", f"传感器 {state.sensor_code} telemetry 发送失败")

                    state.next_publish_monotonic = now_monotonic + state.telemetry_interval_seconds

                if state.heartbeat.should_publish(now_monotonic):
                    status_payload = state.build_status_payload()
                    status_ok = self._publish(f"streetlight/{state.sensor_code}/status", status_payload)
                    published_at = datetime.now()
                    state.heartbeat.mark_published(published_at)
                    state.heartbeat.schedule_next(now_monotonic)
                    if status_ok:
                        self.append_log(
                            "INFO",
                            f"传感器 {state.sensor_code} 已发送 status online={state.online}",
                        )
                    else:
                        self.append_log("WARN", f"传感器 {state.sensor_code} status 发送失败")

            self._stop_event.wait(0.5)

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        is_failure = getattr(reason_code, "is_failure", False)
        if callable(is_failure):
            is_failure = is_failure()
        if is_failure:
            self._connected = False
            self.append_log("ERROR", f"传感器模拟器 MQTT 连接失败: {reason_code}")
            return

        self._connected = True
        client.subscribe("streetlight/+/command")
        self.append_log("INFO", "传感器模拟器已连接 Broker 并订阅 command")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        self._connected = False
        self.append_log("WARN", f"传感器模拟器 MQTT 连接断开: {reason_code}")

    def _on_message(self, client, userdata, message) -> None:
        if not message.topic.endswith("/command"):
            return

        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except Exception:
            self.append_log("ERROR", f"收到无法解析的命令消息: {message.topic}")
            return

        sensor_code = message.topic.split("/")[1]
        with self._lock:
            state = next((item for item in self._sensors.values() if item.sensor_code == sensor_code), None)
            if state is None:
                self._logs.appendleft(
                    SimulatorLogEntry(
                        created_at=datetime.now(),
                        level="WARN",
                        message=f"收到未知传感器命令: {sensor_code}",
                    )
                )
                return

            state.apply_command(payload)
            self._logs.appendleft(
                SimulatorLogEntry(
                    created_at=datetime.now(),
                    level="INFO",
                    message=f"传感器 {sensor_code} 已接收命令 {state.last_command}",
                )
            )


simulator_manager = SimulatorManager()
