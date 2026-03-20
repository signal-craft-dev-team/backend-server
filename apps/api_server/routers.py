from __future__ import annotations

import os
from datetime import timedelta
from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

try:
    import google.auth
    from google.auth import credentials as google_auth_credentials
    from google.auth.transport.requests import Request as GoogleAuthRequest
except ImportError:  # pragma: no cover - optional dependency
    google.auth = None  # type: ignore[assignment]
    google_auth_credentials = None  # type: ignore[assignment]
    GoogleAuthRequest = None  # type: ignore[assignment]

try:
    from google.cloud import storage
except ImportError:  # pragma: no cover - optional dependency
    storage = None  # type: ignore[assignment]

try:
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:  # pragma: no cover - optional dependency
    DefaultCredentialsError = Exception  # type: ignore[assignment]


# APIRouter 인스턴스 생성: 이 모듈의 라우트를 묶는 역할
router = APIRouter()


# ---------------------------------------------------------------------------
# 요청/응답 모델
# ---------------------------------------------------------------------------


class PresignedUploadRequest(BaseModel):
    # 클라이언트가 presign 요청 시 전달하는 메타데이터 모델
    device_id: str
    sequence: int
    timestamp_ms: int
    file_name: str
    content_type: str
    byte_length: int


class PresignedUploadResponse(BaseModel):
    # presign 응답에 포함되는 필드 모델
    upload_url: str
    object_path: str
    upload_session_id: str
    expires_in_seconds: int


# ---------------------------------------------------------------------------
# Presigned URL 발급 서비스 (POC용)
# - GCS 자격증명이 있으면 실제 서명 URL 생성
# - 없으면 테스트 가능한 fallback URL을 반환
# ---------------------------------------------------------------------------


class PresignedUrlService:
    """간단한 Presigned URL 발급 서비스 (POC용).

    실제 GCS 자격증명이 구성되어 있으면 서명 URL을 생성하고,
    그렇지 않으면 테스트 가능한 디폴트 URL을 반환합니다.
    """

    def __init__(
        self,
        bucket_name: str | None,
        url_expiration_seconds: int,
        object_prefix: str,
        project_id: str | None = None,
        storage_client=None,
    ) -> None:
        # 인스턴스 설정 초기화
        self.bucket_name = bucket_name
        self.url_expiration_seconds = url_expiration_seconds
        self.object_prefix = object_prefix.strip("/") if object_prefix else ""
        self.project_id = project_id
        self.credentials = None
        self.auth_request = GoogleAuthRequest() if GoogleAuthRequest is not None else None
        # 외부에서 주입된 storage client 우선 사용
        self.storage_client = storage_client if storage_client is not None else self._build_client()
        if self.storage_client is not None and self.credentials is None:
            self.credentials = getattr(self.storage_client, "_credentials", None)

    @classmethod
    def from_env(cls) -> "PresignedUrlService":
        # 환경변수에서 설정을 읽어 서비스 인스턴스 생성
        bucket = os.getenv("GCS_AUDIO_BUCKET")
        expires = int(os.getenv("GCS_SIGNED_URL_EXPIRATION_SECONDS", "3600"))
        prefix = os.getenv("GCS_UPLOAD_PREFIX", "uploads")
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        return cls(bucket, expires, prefix, project_id=project)

    def _build_client(self):
        # google cloud storage 클라이언트를 생성하거나 None을 반환
        if storage is None or not self.bucket_name:
            return None
        try:
            credentials = None
            detected_project_id = self.project_id

            if google.auth is not None:
                credentials, detected_project_id = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                self.credentials = credentials

            if not self.project_id and detected_project_id:
                self.project_id = detected_project_id

            return storage.Client(project=self.project_id, credentials=credentials)
        except DefaultCredentialsError:
            return None
        except Exception:
            return None

    def _build_signed_url(self, blob, content_type: str) -> str:
        if (
            self.credentials is not None
            and google_auth_credentials is not None
            and not isinstance(self.credentials, google_auth_credentials.Signing)
        ):
            if self.auth_request is None:
                raise RuntimeError("google-auth transport request is unavailable")

            if not getattr(self.credentials, "valid", False):
                self.credentials.refresh(self.auth_request)

            service_account_email = getattr(self.credentials, "service_account_email", None)
            access_token = getattr(self.credentials, "token", None)

            if access_token and service_account_email:
                return blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(seconds=self.url_expiration_seconds),
                    method="PUT",
                    content_type=content_type,
                    credentials=self.credentials,
                    service_account_email=service_account_email,
                    access_token=access_token,
                )

        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=self.url_expiration_seconds),
            method="PUT",
            content_type=content_type,
        )

    def _build_object_path(self, request: PresignedUploadRequest) -> str:
        # 안전한 object path 생성: prefix/device_id/file_name
        safe_file_name = PurePosixPath(request.file_name).name or f"{request.sequence}.wav"
        return str(PurePosixPath(self.object_prefix) / request.device_id / safe_file_name)

    def _build_fallback_response(
        self,
        request: PresignedUploadRequest,
        object_path: str,
        upload_session_id: str,
    ) -> PresignedUploadResponse:
        return PresignedUploadResponse(
            upload_url=f"https://storage.googleapis.com/{self.bucket_name or 'missing-bucket'}/{object_path}",
            object_path=object_path,
            upload_session_id=upload_session_id,
            expires_in_seconds=self.url_expiration_seconds,
        )

    def issue_upload(self, request: PresignedUploadRequest) -> PresignedUploadResponse:
        # 업로드 세션 ID 생성 및 서명 URL 반환 로직
        upload_session_id = str(uuid4())
        object_path = self._build_object_path(request)

        # 스토리지 클라이언트가 준비되지 않았으면 dry-run URL 반환
        if self.storage_client is None or not self.bucket_name:
            return self._build_fallback_response(request, object_path, upload_session_id)

        # 실제 GCS 서명 URL 생성
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(object_path)
        upload_url = self._build_signed_url(blob, request.content_type)

        return PresignedUploadResponse(
            upload_url=upload_url,
            object_path=object_path,
            upload_session_id=upload_session_id,
            expires_in_seconds=self.url_expiration_seconds,
        )

    def response_dict(self, request: PresignedUploadRequest) -> dict[str, object]:
        return self.issue_upload(request).model_dump()


# ---------------------------------------------------------------------------
# 라우트: presigned URL 발급
# - JSON body로 요청을 받고, PresignedUrlService를 통해 결과 반환
# ---------------------------------------------------------------------------


@router.post("/uploads/presign", response_model=PresignedUploadResponse)
async def issue_presigned_upload(request_body: PresignedUploadRequest) -> PresignedUploadResponse:
    """Presigned URL을 발급합니다 (POC).

    요청 본문으로 업로드 요청 메타데이터를 받습니다. 실제 스토리지
    자격증명이 구성되어 있지 않으면 테스트 가능한 URL을 반환합니다.
    """

    # 환경에서 설정을 읽어 서비스 인스턴스 생성 후 응답 반환
    service = PresignedUrlService.from_env()
    return service.issue_upload(request_body)
