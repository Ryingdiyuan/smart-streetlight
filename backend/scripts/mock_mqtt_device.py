import argparse
import json
import os
import random
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"

DEFAULT_PROFILES = {
    "SL-001": {"base_light": 85, "variance": 25, "voltage": 220.4},
    "SL-002": {"base_light": 160, "variance": 35, "voltage": 221.0},
    "SL-003": {"base_light": 120, "variance": 45, "voltage": 219.8},
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clamp(value: float, minimum: int, maximum: int) -> int:
    return int(max(minimum, min(maximum, round(value))))


@dataclass
class SimulatedDevice:
    device_id: str
    base_light: int
    variance: int
    voltage_base: float
    lamp_status: str = "off"
    brightness: int = 0
    online: bool = True

    def apply_command(self, payload: dict[str, object]) -> None:
        command = str(payload.get("command", "")).upper()
        if command == "TURN_ON":
            self.lamp_status = "on"
            self.brightness = max(self.brightness, 80)
        elif command == "TURN_OFF":
            self.lamp_status = "off"
            self.brightness = 0
        elif command == "SET_BRIGHTNESS":
            raw_value = payload.get("brightness", 0)
            value = clamp(float(raw_value), 0, 100)
            self.brightness = value
            self.lamp_status = "on" if value > 0 else "off"

    def build_telemetry(self) -> dict[str, object]:
        ambient = self.base_light + random.randint(-self.variance, self.variance)
        lamp_boost = 0
        if self.lamp_status == "on":
            lamp_boost = max(30, int(self.brightness * 1.6))

        light_intensity = clamp(ambient + lamp_boost, 0, 1000)
        voltage = round(self.voltage_base + random.uniform(-1.2, 1.2), 1)

        return {
            "deviceId": self.device_id,
            "lightIntensity": light_intensity,
            "lampStatus": self.lamp_status,
            "voltage": voltage,
            "timestamp": now_text(),
        }

    def build_status(self) -> dict[str, object]:
        return {
            "deviceId": self.device_id,
            "online": self.online,
            "lampStatus": self.lamp_status,
            "timestamp": now_text(),
        }


class DeviceSimulator:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.running = True
        self.devices = self._build_devices(args.devices)
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=args.client_id,
        )
        if args.username:
            self.client.username_pw_set(args.username, args.password)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def _build_devices(self, devices_text: str) -> dict[str, SimulatedDevice]:
        devices: dict[str, SimulatedDevice] = {}
        for raw_code in devices_text.split(","):
            code = raw_code.strip()
            if not code:
                continue
            profile = DEFAULT_PROFILES.get(
                code,
                {"base_light": 110, "variance": 30, "voltage": 220.0},
            )
            devices[code] = SimulatedDevice(
                device_id=code,
                base_light=int(profile["base_light"]),
                variance=int(profile["variance"]),
                voltage_base=float(profile["voltage"]),
            )
        if not devices:
            raise ValueError("At least one device code is required")
        return devices

    def on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        is_failure = getattr(reason_code, "is_failure", False)
        if callable(is_failure):
            is_failure = is_failure()
        if is_failure:
            print(f"[mqtt] connect failed: {reason_code}", flush=True)
            return

        print(
            f"[mqtt] connected to {self.args.host}:{self.args.port}, subscribe streetlight/+/command",
            flush=True,
        )
        client.subscribe("streetlight/+/command")

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties) -> None:
        print(f"[mqtt] disconnected: {reason_code}", flush=True)

    def on_message(self, client, userdata, message) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            print(f"[command] ignore invalid payload topic={message.topic}", flush=True)
            return

        parts = message.topic.split("/")
        if len(parts) < 3:
            return

        device_id = parts[1]
        device = self.devices.get(device_id)
        if device is None:
            return

        device.apply_command(payload)
        print(
            f"[command] {device_id} <= {payload.get('command')} | lamp={device.lamp_status} brightness={device.brightness}",
            flush=True,
        )

    def publish_json(self, topic: str, payload: dict[str, object]) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        result = self.client.publish(topic, text, qos=self.args.qos)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"[mqtt] publish failed topic={topic} rc={result.rc}", flush=True)
            return
        print(f"[mqtt] publish {topic} {text}", flush=True)

    def publish_cycle(self, cycle_index: int) -> None:
        for device in self.devices.values():
            if cycle_index % self.args.status_every == 0:
                self.publish_json(
                    f"streetlight/{device.device_id}/status",
                    device.build_status(),
                )

            self.publish_json(
                f"streetlight/{device.device_id}/telemetry",
                device.build_telemetry(),
            )

    def stop(self, *_args) -> None:
        self.running = False

    def run(self) -> int:
        print(
            f"[simulator] devices={','.join(self.devices.keys())} interval={self.args.interval}s status_every={self.args.status_every}",
            flush=True,
        )
        self.client.connect(self.args.host, self.args.port, keepalive=60)
        self.client.loop_start()

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        cycle_index = 0
        try:
            while self.running:
                cycle_index += 1
                self.publish_cycle(cycle_index)
                if self.args.count and cycle_index >= self.args.count:
                    break
                time.sleep(self.args.interval)
        finally:
            self.client.loop_stop()
            self.client.disconnect()

        print("[simulator] stopped", flush=True)
        return 0


def parse_args() -> argparse.Namespace:
    load_dotenv(ENV_FILE)

    parser = argparse.ArgumentParser(
        description="模拟智慧路灯设备通过 MQTT 周期上报 telemetry/status，并接收 command。",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("MQTT_HOST", "127.0.0.1"),
        help="MQTT Broker 地址，默认读取 backend/.env 的 MQTT_HOST",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MQTT_PORT", "1883")),
        help="MQTT Broker 端口，默认读取 backend/.env 的 MQTT_PORT",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("MQTT_USERNAME", ""),
        help="MQTT 用户名，默认读取 backend/.env 的 MQTT_USERNAME",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("MQTT_PASSWORD", ""),
        help="MQTT 密码，默认读取 backend/.env 的 MQTT_PASSWORD",
    )
    parser.add_argument(
        "--client-id",
        default=f"smart-streetlight-simulator-{os.getpid()}",
        help="MQTT client id",
    )
    parser.add_argument(
        "--devices",
        default="SL-001,SL-002,SL-003",
        help="模拟设备编码，逗号分隔，必须与 devices.device_code 一致",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="每轮 telemetry 上报间隔秒数",
    )
    parser.add_argument(
        "--status-every",
        type=int,
        default=1,
        help="每多少轮发送一次 status 心跳，默认每轮都发",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="发送轮数，0 表示持续运行",
    )
    parser.add_argument(
        "--qos",
        type=int,
        choices=(0, 1),
        default=0,
        help="MQTT 发布 QoS",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="随机种子，便于复现实验结果",
    )
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    return args


if __name__ == "__main__":
    try:
        simulator = DeviceSimulator(parse_args())
    except ValueError as error:
        print(f"[simulator] invalid arguments: {error}", flush=True)
        sys.exit(2)

    try:
        sys.exit(simulator.run())
    except OSError as error:
        print(f"[simulator] failed to connect mqtt broker: {error}", flush=True)
        sys.exit(1)
