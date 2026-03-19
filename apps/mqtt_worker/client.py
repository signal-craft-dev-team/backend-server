from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import logging
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

logger = logging.getLogger(__name__)

# aiomqtt를 동적으로 로드합니다. 설치되지 않았으면 None으로 둡니다.
try:
    aiomqtt = importlib.import_module("aiomqtt")
except ImportError:  # pragma: no cover - dependency may not be installed yet
    aiomqtt = None  # type: ignore[assignment]

# 클라우드 전용 타입들을 안전하게 임포트하되, 없으면 대체 구현을 제공합니다.
try:
    from core.settings import CloudBackendSettings
    from core.firestore import (
        FirestoreIngestRecord,
        FirestoreRepository,
        utc_now,
    )
except Exception:  # pragma: no cover - may not be available in this workspace
    # CloudBackendSettings가 없을 때 타입 체크와 런타임 안전성을 위해 간단한 스텁을 제공합니다.
    @dataclass
    class _CloudBackendSettingsStub:
        mqtt_topic_device_telemetry: str = "device/#"
        mqtt_broker_host: str = "localhost"
        mqtt_broker_port: int = 1883
        mqtt_broker_username: str | None = None
        mqtt_broker_password: str | None = None
        mqtt_reconnect_delay_seconds: float = 2.0
        mqtt_client_id_prefix: str = "signal-craft-cloud"

    CloudBackendSettings = _CloudBackendSettingsStub  # type: ignore

    # FirestoreIngestRecord 대체형: 실제 필드와 유사하게 정의합니다.
    @dataclass(frozen=True)
    class FirestoreIngestRecord:
        installation_id: str
        hw_device_id: str | None
        trace_id: str
        topic: str
        contract_version: str
        payload: dict[str, Any]
        received_at: Any

    # 간단한 저장소 대체 구현: save_telemetry를 구현합니다.
    class FirestoreRepository:
        def save_telemetry(self, record: FirestoreIngestRecord) -> dict[str, Any]:
            # 실제 저장 대신 결과 형식(로그용)을 흉내냅니다.
            return {
                "installation_document_id": getattr(record, "installation_id", "dummy"),
                "log_document": {"trace_id": getattr(record, "trace_id", "dummy")},
                "mode": "ingest",
            }

    # utc_now 대체 구현
    def utc_now():
        import datetime

        return datetime.datetime.utcnow()


# MQTT 토픽의 루트 값
TOPIC_ROOT = "device"


@dataclass(frozen=True)
class IncomingMqttMessage:
    """MQTT 수신 메시지를 표현하는 단순 데이터 클래스"""

    topic: str
    payload_bytes: bytes


# 토픽에서 installation id 추출 (예: device/{installation_id}/...)
def extract_installation_id_from_topic(topic: str) -> str:
    parts = topic.split("/")
    if len(parts) < 2:
        raise ValueError(f"unexpected topic format: {topic}")
    if parts[0] != TOPIC_ROOT or not parts[1]:
        raise ValueError(f"unsupported topic pattern: {topic}")
    return parts[1]


# 토픽의 접미사(루트 이후 부분) 추출
def extract_topic_suffix(topic: str) -> tuple[str, ...]:
    parts = topic.split("/")
    if len(parts) < 2 or parts[0] != TOPIC_ROOT:
        raise ValueError(f"unsupported topic pattern: {topic}")
    return tuple(parts[2:])


# 바이트 페이로드를 JSON 객체로 디코드하고 검증
def decode_payload(payload_bytes: bytes) -> dict[str, Any]:
    payload = json.loads(payload_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("mqtt payload must decode to an object")
    return payload


# 하드웨어 장치 ID를 페이로드에서 해석 (hw_device_id 우선, legacy device_id 지원)
def resolve_hw_device_id(payload: dict[str, Any]) -> str | None:
    hw_device_id = payload.get("hw_device_id")
    if isinstance(hw_device_id, str) and hw_device_id:
        return hw_device_id

    legacy_device_id = payload.get("device_id")
    if isinstance(legacy_device_id, str) and legacy_device_id:
        return legacy_device_id

    return None


# 트레이스 ID가 명시되어 있으면 사용하고, 없으면 페이로드와 토픽으로 생성
def resolve_trace_id(topic: str, payload: dict[str, Any]) -> str:
    trace_id = payload.get("trace_id")
    if isinstance(trace_id, str) and trace_id:
        return trace_id

    digest = hashlib.sha256(f"{topic}:{json.dumps(payload, sort_keys=True)}".encode("utf-8")).hexdigest()
    return f"generated-{digest[:16]}"


# 계약 버전을 페이로드에서 읽고, ping 토픽이면 v0-ping, 기본은 v0-unversioned
def resolve_contract_version(payload: dict[str, Any], topic_suffix: tuple[str, ...]) -> str:
    contract_version = payload.get("contract_version")
    if isinstance(contract_version, str) and contract_version:
        return contract_version
    if topic_suffix and topic_suffix[-1] == "ping":
        return "v0-ping"
    return "v0-unversioned"


class MqttConsumerWorker:
    """멀티토픽(MQTT wildcard) 소비자: 수신 메시지를 정규화하고 저장소에 전달합니다.

    - repository: save_telemetry(record) 메서드를 갖는 객체
    - consume_forever(): aiomqtt를 사용해 메시지를 지속적으로 수신
    """

    def __init__(
        self,
        repository: Any,
        topic_pattern: str = "device/#",
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        reconnect_delay_seconds: float = 2.0,
        client_id_prefix: str = "signal-craft-cloud",
    ) -> None:
        # 인스턴스 변수 초기화
        self.repository = repository
        self.topic_pattern = topic_pattern
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.reconnect_delay_seconds = reconnect_delay_seconds
        self.client_id_prefix = client_id_prefix
        self._stop_event = asyncio.Event()

    @classmethod
    def from_settings(cls, settings, repository) -> "MqttConsumerWorker":
        # 설정 객체로부터 Worker 인스턴스를 생성하는 헬퍼
        return cls(
            repository=repository,
            topic_pattern=settings.mqtt_topic_device_telemetry,
            broker_host=settings.mqtt_broker_host,
            broker_port=settings.mqtt_broker_port,
            username=settings.mqtt_broker_username,
            password=settings.mqtt_broker_password,
            reconnect_delay_seconds=settings.mqtt_reconnect_delay_seconds,
            client_id_prefix=settings.mqtt_client_id_prefix,
        )

    def normalize_message(self, message: IncomingMqttMessage) -> FirestoreIngestRecord:
        # 수신 메시지를 FirestoreIngestRecord 형태로 정규화
        installation_id = extract_installation_id_from_topic(message.topic)
        topic_suffix = extract_topic_suffix(message.topic)
        payload = decode_payload(message.payload_bytes)

        return FirestoreIngestRecord(
            installation_id=installation_id,
            hw_device_id=resolve_hw_device_id(payload),
            trace_id=resolve_trace_id(message.topic, payload),
            topic=message.topic,
            contract_version=resolve_contract_version(payload, topic_suffix),
            payload=payload,
            received_at=utc_now(),
        )

    def handle_message(self, message: IncomingMqttMessage) -> dict[str, Any]:
        # 메시지를 정규화하고 저장소에 저장한 뒤 결과를 반환
        record = self.normalize_message(message)
        return self.repository.save_telemetry(record)

    async def consume_forever(self) -> None:
        # aiomqtt가 설치되지 않으면 예외 발생
        if aiomqtt is None:
            raise RuntimeError(
                "aiomqtt is not installed. Install runtime dependencies inside cloud/.venv before starting the consumer."
            )

        while not self._stop_event.is_set():
            try:
                await self._consume_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("mqtt consumer loop failed; retrying")
                await asyncio.sleep(self.reconnect_delay_seconds)

    async def _consume_once(self) -> None:
        # MQTT 브로커에 연결하고, 구독한 토픽의 메시지를 처리합니다.
        client_id = f"{self.client_id_prefix}-ingest"
        logger.info(
            "connecting mqtt consumer host=%s port=%s topic=%s",
            self.broker_host,
            self.broker_port,
            self.topic_pattern,
        )

        async with aiomqtt.Client(
            hostname=self.broker_host,
            port=self.broker_port,
            username=self.username,
            password=self.password,
            identifier=client_id,
        ) as client:
            await client.subscribe(self.topic_pattern)
            logger.info("mqtt consumer subscribed topic=%s", self.topic_pattern)

            async for message in client.messages:
                if self._stop_event.is_set():
                    return

                topic = getattr(message.topic, "value", str(message.topic))
                payload_bytes = bytes(message.payload)
                result = self.handle_message(
                    IncomingMqttMessage(topic=topic, payload_bytes=payload_bytes)
                )
                logger.info(
                    "mqtt message persisted installation_id=%s trace_id=%s mode=%s",
                    result["installation_document_id"],
                    result["log_document"]["trace_id"],
                    result["mode"],
                )

    async def stop(self) -> None:
        # 외부에서 호출하여 루프를 종료시키는 메서드
        self._stop_event.set()


# 시작점: FastAPI lifespan에서 사용될 비동기 함수
async def start_mqtt_loop() -> None:
    """백그라운드에서 MQTT 수신 루프를 실행합니다.

    - 가능한 경우 실제 `FirestoreRepository`를 사용하고, 실패하면 대체 저장소를 사용합니다.
    - 취소 이벤트 발생 시 안전하게 종료합니다.
    """
    logger.info("MQTT worker: start_mqtt_loop starting")

    settings = CloudBackendSettings.from_env()

    if not settings.mqtt_consumer_enabled:
        logger.info("MQTT consumer disabled by MQTT_CONSUMER_ENABLED=false; skipping start")
        return

    # 저장소 초기화 시도: 실제 구현이 없으면 대체 구현 사용
    try:
        repo = FirestoreRepository.from_settings(settings)
    except Exception:
        logger.info("FirestoreRepository not available; using fallback dummy repository")

        class _DummyRepo:
            def save_telemetry(self, record: FirestoreIngestRecord) -> dict[str, Any]:
                return {
                    "installation_document_id": getattr(record, "installation_id", "dummy"),
                    "log_document": {"trace_id": getattr(record, "trace_id", "dummy")},
                    "mode": "ingest",
                }

        repo = _DummyRepo()

    worker = MqttConsumerWorker.from_settings(settings, repository=repo)

    try:
        await worker.consume_forever()
    except asyncio.CancelledError:
        logger.info("MQTT worker: start_mqtt_loop cancelled, shutting down")
        raise
    except Exception:
        logger.exception("MQTT worker: unexpected error in start_mqtt_loop")