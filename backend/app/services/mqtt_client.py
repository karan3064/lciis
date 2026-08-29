"""Publishes alert JSON payloads to the Mosquitto MQTT broker. Bedside
Alert Pagers (ESP32-S3) subscribe to `<prefix>/<bed>` and render whatever
lands there (see hl7/ and firmware docs for the wire format)."""

import json
import logging
from datetime import datetime
from typing import Optional

import paho.mqtt.client as mqtt

from app.config import settings

logger = logging.getLogger("lciis.mqtt")

_client: Optional[mqtt.Client] = None


def get_client() -> mqtt.Client:
    global _client
    if _client is None:
        _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        try:
            _client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=30)
            _client.loop_start()
        except Exception:
            logger.exception("MQTT broker unreachable at %s:%s — alerts will be "
                              "logged but not delivered to bedside devices",
                              settings.mqtt_host, settings.mqtt_port)
    return _client


def publish_alert(
    bed: Optional[str],
    patient_id: str,
    patient_name: str,
    test_name: str,
    severity: str,
    message: str,
    suggested_action: str,
) -> None:
    topic = f"{settings.mqtt_alert_topic_prefix}/{bed or 'unassigned'}"
    payload = json.dumps(
        {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "test_name": test_name,
            "severity": severity,
            "message": message,
            "suggested_action": suggested_action,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )
    try:
        client = get_client()
        client.publish(topic, payload, qos=1)
    except Exception:
        logger.exception("Failed to publish alert to MQTT topic %s", topic)
