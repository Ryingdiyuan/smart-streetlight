import logging

import paho.mqtt.client as mqtt

from app.core.config import settings

logger = logging.getLogger(__name__)


class MqttClient:
    def __init__(self) -> None:
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, settings.mqtt_client_id)
        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    def start(self) -> None:
        logger.info("Starting MQTT client %s:%s", settings.mqtt_host, settings.mqtt_port)
        self._client.connect(settings.mqtt_host, settings.mqtt_port)
        self._client.loop_start()

    def stop(self) -> None:
        logger.info("Stopping MQTT client")
        self._client.loop_stop()
        self._client.disconnect()


mqtt_client = MqttClient()
