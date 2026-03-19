from __future__ import annotations

from dataclasses import dataclass
from os import getenv


def _env_bool(name: str, default: bool) -> bool:
    raw = getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class CloudBackendSettings:
    mqtt_broker_host: str
    mqtt_broker_port: int
    mqtt_broker_username: str | None
    mqtt_broker_password: str | None
    mqtt_topic_device_telemetry: str
    telemetry_collection: str
    firestore_database: str
    google_cloud_project: str | None
    gcs_audio_bucket: str | None
    gcs_signed_url_expiration_seconds: int
    gcs_audio_prefix: str
    fastapi_host: str
    fastapi_port: int
    log_level: str
    mqtt_consumer_enabled: bool
    mqtt_reconnect_delay_seconds: float
    mqtt_client_id_prefix: str

    @classmethod
    def from_env(cls) -> "CloudBackendSettings":
        return cls(
            mqtt_broker_host=getenv("MQTT_BROKER_HOST", "localhost"),
            mqtt_broker_port=int(getenv("MQTT_BROKER_PORT", "1883")),
            mqtt_broker_username=getenv("MQTT_BROKER_USERNAME") or None,
            mqtt_broker_password=getenv("MQTT_BROKER_PASSWORD") or None,
            mqtt_topic_device_telemetry=getenv("MQTT_TOPIC_DEVICE_TELEMETRY", "device/#"),
            telemetry_collection=getenv("FIRESTORE_COLLECTION_TELEMETRY", "device_telemetry"),
            firestore_database=getenv("FIRESTORE_DATABASE", "(default)"),
            google_cloud_project=getenv("GOOGLE_CLOUD_PROJECT") or None,
            gcs_audio_bucket=getenv("GCS_AUDIO_BUCKET") or None,
            gcs_signed_url_expiration_seconds=int(getenv("GCS_SIGNED_URL_EXPIRATION_SECONDS", "900")),
            gcs_audio_prefix=getenv("GCS_AUDIO_PREFIX", "raw-audio"),
            fastapi_host=getenv("FASTAPI_HOST", "0.0.0.0"),
            fastapi_port=int(getenv("FASTAPI_PORT", "8000")),
            log_level=getenv("LOG_LEVEL", "INFO"),
            mqtt_consumer_enabled=_env_bool("MQTT_CONSUMER_ENABLED", True),
            mqtt_reconnect_delay_seconds=float(getenv("MQTT_RECONNECT_DELAY_SECONDS", "2.0")),
            mqtt_client_id_prefix=getenv("MQTT_CLIENT_ID_PREFIX", "signal-craft-cloud"),
        )