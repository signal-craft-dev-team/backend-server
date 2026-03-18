from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

try:
    from google.cloud import firestore
except ImportError:  # pragma: no cover - dependency may not be installed yet
    firestore = None  # type: ignore[assignment]

from core.settings import CloudBackendSettings


SEOUL_TZ = ZoneInfo("Asia/Seoul")


def _to_seoul(value: datetime) -> datetime:
    return value.astimezone(SEOUL_TZ)


def _isoformat_seoul(value: datetime) -> str:
    return _to_seoul(value).isoformat(timespec="milliseconds")


def _timestamp_document_id(value: datetime, trace_id: str) -> str:
    timestamp_part = _to_seoul(value).strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]
    trace_suffix = trace_id.replace("/", "-")[:8] if trace_id else "event"
    return f"{timestamp_part}__{trace_suffix}"


@dataclass(frozen=True)
class FirestoreIngestRecord:
    installation_id: str
    hw_device_id: str | None
    trace_id: str
    topic: str
    contract_version: str
    payload: dict[str, Any]
    received_at: datetime


class FirestoreRepository:
    """Validated multi-device telemetry writer.

    When the Firestore client library is unavailable or credentials are not yet
    configured, writes degrade to a dry-run response so the ingest flow can be
    exercised without mutating storage.
    """

    def __init__(
        self,
        telemetry_collection: str = "device-telemetry-db",
        database: str = "(default)",
        project_id: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.telemetry_collection = telemetry_collection
        self.database = database
        self.project_id = project_id
        self.client = client if client is not None else self._build_client()

    @classmethod
    def from_settings(cls, settings: CloudBackendSettings) -> "FirestoreRepository":
        return cls(
            telemetry_collection=settings.telemetry_collection,
            database=settings.firestore_database,
            project_id=settings.google_cloud_project,
        )

    def _build_client(self) -> Any | None:
        if firestore is None:
            return None
        return firestore.Client(project=self.project_id, database=self.database)

    def build_installation_document_id(self, record: FirestoreIngestRecord) -> str:
        return record.installation_id

    def build_log_document_id(self, record: FirestoreIngestRecord) -> str:
        return _timestamp_document_id(record.received_at, record.trace_id)

    def build_installation_summary_document(self, record: FirestoreIngestRecord) -> dict[str, Any]:
        return {
            "installation_id": record.installation_id,
            "latest_hw_device_id": record.hw_device_id,
            "latest_trace_id": record.trace_id,
            "latest_topic": record.topic,
            "latest_contract_version": record.contract_version,
            "latest_received_at": _isoformat_seoul(record.received_at),
            "updated_at": _isoformat_seoul(record.received_at),
            "timezone": "Asia/Seoul",
        }

    def build_log_document(self, record: FirestoreIngestRecord) -> dict[str, Any]:
        return {
            "installation_id": record.installation_id,
            "hw_device_id": record.hw_device_id,
            "trace_id": record.trace_id,
            "topic": record.topic,
            "contract_version": record.contract_version,
            "received_at": _isoformat_seoul(record.received_at),
            "timezone": "Asia/Seoul",
            "payload": record.payload,
        }

    def save_telemetry(self, record: FirestoreIngestRecord) -> dict[str, Any]:
        write_plan = {
            "root_collection": self.telemetry_collection,
            "installation_document_id": self.build_installation_document_id(record),
            "installation_document": self.build_installation_summary_document(record),
            "logs_subcollection": "logs",
            "log_document_id": self.build_log_document_id(record),
            "log_document": self.build_log_document(record),
        }
        if self.client is None:
            return {**write_plan, "persisted": False, "mode": "dry-run"}

        installation_ref = self.client.collection(self.telemetry_collection).document(
            write_plan["installation_document_id"]
        )
        installation_ref.set(write_plan["installation_document"], merge=True)
        installation_ref.collection(write_plan["logs_subcollection"]).document(
            write_plan["log_document_id"]
        ).set(
            write_plan["log_document"]
        )
        return {**write_plan, "persisted": True, "mode": "firestore"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)