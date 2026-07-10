import logging
import os
from typing import Any

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.mqtt.handlers import handle_register_message, handle_status_message, handle_telemetry_message

logger = logging.getLogger(__name__)
TELEMETRY_TOPIC = "streetlight/+/telemetry"
STATUS_TOPIC = "streetlight/+/status"
REGISTER_TOPIC = "streetlight/+/register"


def build_runtime_client_id() -> str:
    return f"{settings.mqtt_client_id}-{os.getpid()}"


class MqttClient:
    def __init__(self) -> None:
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            build_runtime_client_id(),
        )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._connected = False
        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    def start(self) -> None:
        logger.info("Starting MQTT client %s:%s", settings.mqtt_host, settings.mqtt_port)
        try:
            self._client.connect(settings.mqtt_host, settings.mqtt_port)
            self._client.loop_start()
        except OSError:
            logger.exception("Failed to connect MQTT broker")

    def stop(self) -> None:
        logger.info("Stopping MQTT client")
        self._client.loop_stop()
        self._client.disconnect()

    def publish(self, topic: str, payload: str | bytes) -> bool:
        if not settings.mqtt_enabled:
            logger.info("MQTT disabled, skip publish topic=%s", topic)
            return False
        if not self._connected:
            logger.warning("MQTT not connected, publish failed topic=%s", topic)
            return False

        try:
            result = self._client.publish(topic, payload)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception:
            logger.exception("Failed to publish MQTT message topic=%s", topic)
            return False

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        is_failure = getattr(reason_code, "is_failure", False)
        if callable(is_failure):
            is_failure = is_failure()
        if is_failure:
            logger.error("MQTT connection failed: %s", reason_code)
            self._connected = False
            return

        self._connected = True
        logger.info(
            "MQTT connected, subscribing %s, %s and %s",
            TELEMETRY_TOPIC,
            STATUS_TOPIC,
            REGISTER_TOPIC,
        )
        client.subscribe(TELEMETRY_TOPIC)
        client.subscribe(STATUS_TOPIC)
        client.subscribe(REGISTER_TOPIC)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        self._connected = False
        logger.info("MQTT disconnected: %s", reason_code)

    def _on_message(self, client, userdata, message) -> None:
        if message.topic.endswith("/telemetry"):
            handle_telemetry_message(message.topic, message.payload)
        elif message.topic.endswith("/status"):
            handle_status_message(message.topic, message.payload)
        elif message.topic.endswith("/register"):
            handle_register_message(message.topic, message.payload)


mqtt_client = MqttClient()
