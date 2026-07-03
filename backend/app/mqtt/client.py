import logging

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.mqtt.handlers import handle_telemetry_message

logger = logging.getLogger(__name__)
TELEMETRY_TOPIC = "streetlight/+/telemetry"


class MqttClient:
    def __init__(self) -> None:
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, settings.mqtt_client_id)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
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

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        is_failure = getattr(reason_code, "is_failure", False)
        if callable(is_failure):
            is_failure = is_failure()
        if is_failure:
            logger.error("MQTT connection failed: %s", reason_code)
            return

        logger.info("MQTT connected, subscribing %s", TELEMETRY_TOPIC)
        client.subscribe(TELEMETRY_TOPIC)

    def _on_message(self, client, userdata, message) -> None:
        if message.topic.endswith("/telemetry"):
            handle_telemetry_message(message.topic, message.payload)


mqtt_client = MqttClient()
