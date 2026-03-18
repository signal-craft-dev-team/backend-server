# Feature Specification: Boilerplate Implementation

**Feature Branch**: `001-boilerplate-backend`  
**Created**: 2026-03-18  
**Status**: Draft  
**Input**: User description:

```
/speckit.specify
# Specify: Boilerplate Implementation

## 1. Directory Structure
아래의 디렉토리 구조와 빈 `__init__.py` 파일들을 생성하라.
/
├── core/
│   └── __init__.py
├── apps/
│   ├── __init__.py
│   ├── api_server/
│   │   └── __init__.py
│   └── mqtt_worker/
│       └── __init__.py
└── main.py

## 2. Feature 1: MQTT Worker (apps/mqtt_worker/client.py)
- 디바이스 고장 진단 신호를 수신하는 백그라운드 워커 모듈이다.
- `start_mqtt_loop()` 비동기 함수를 구현하라.
- 이 함수 내부에 `while True:` 루프와 `await asyncio.sleep(5)`를 사용하여 MQTT 리스너를 시뮬레이션하고, `asyncio.CancelledError` 발생 시 안전하게 종료되도록 `try-except` 처리하라.

## 3. Feature 2: API Server (apps/api_server/routers.py)
- 클라이언트에게 Presigned URL을 발급하는 REST API 모듈이다.
- FastAPI의 `APIRouter()` 인스턴스를 생성하고 변수명은 `router`로 지정하라.
- GET `/presigned-url` 엔드포인트를 만들고, 더미 URL과 상태값을 JSON 형태로 반환하도록 작성하라.

## 4. Entry Point (main.py)
- 프로젝트의 최상위 실행 파일이다.
- **Lifespan Context Manager:** - 앱 시작 시: `apps.mqtt_worker.client`에서 `start_mqtt_loop`를 임포트 시도한다. 성공하면 백그라운드 태스크로 실행하고, 실패(ImportError)하면 건너뛴다.
  - 앱 종료 시: 실행 중인 워커 태스크가 있다면 `cancel()`을 호출하여 안전하게 종료한다.
- **FastAPI Instance:** `lifespan`을 연결하여 `app` 객체를 생성한다.
- **Router Include:** - `apps.api_server.routers`에서 `router`를 임포트 시도한다. 
  - 성공하면 `app.include_router()`를 사용해 `/api/v1` prefix로 연결하고, 실패하면 건너뛴다.
- **Health Check:** GET `/health` 엔드포인트를 구현하여 서버 상태를 반환하라.

향후에 새로운 기능이 추가될수 있음을 염두에 두고 설계를 진행할것
```

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Run reliably with missing feature modules (Priority: P1)

As a developer, I can start the server locally even when some `apps/` submodules are not present (git sparse-checkout), so I can work on a single feature without checking out the whole monorepo.

**Why this priority**: Enables fast local iteration and satisfies the project's Graceful Degradation principle.

**Independent Test**: Remove or rename `apps/mqtt_worker` and/or `apps/api_server`, start the application (`uvicorn main:app`), and verify `/health` returns 200.

**Acceptance Scenarios**:

1. **Given** `apps/mqtt_worker` is absent, **When** the app starts, **Then** startup completes and `/health` returns `{ "status": "ok" }`.
2. **Given** `apps/api_server` is absent, **When** the app starts, **Then** startup completes and no router is mounted at `/api/v1`.

---

### User Story 2 - Issue presigned URLs via API (Priority: P2)

As an API client, I can request a presigned upload URL so the client can upload device diagnostics artifacts.

**Why this priority**: Provides a minimal API surface for clients to upload artifacts used by downstream processing.

**Independent Test**: With `apps/api_server` present, send GET `/api/v1/presigned-url` and expect a JSON response containing keys `url` and `status` with `status == "ok"`.

**Acceptance Scenarios**:

1. **Given** `apps/api_server` is available, **When** GET `/api/v1/presigned-url` is called, **Then** the response is `200` and contains `{ "url": "<string>", "status": "ok" }`.

---

### User Story 3 - Background MQTT worker lifecycle (Priority: P3)

As an operator, I want the MQTT worker to run in the background when present and to shut down cleanly during application shutdown.

**Why this priority**: Ensures background processing doesn't leak resources and supports safe deployments.

**Independent Test**: Start the app with the MQTT worker present, then stop the app; verify logs show cancellation/cleanup messages and the process exits without hanging.

**Acceptance Scenarios**:

1. **Given** `apps/mqtt_worker` is available, **When** the app starts, **Then** a background task `start_mqtt_loop()` is created and runs.
2. **Given** the app receives a shutdown event, **When** shutdown proceeds, **Then** the background task is cancelled and the app exits within 10 seconds.

---

### Edge Cases

- Missing `apps/` directories (sparse-checkout): server must still start.
- Worker raises an exception during runtime: application logs the error and continues to serve API endpoints where possible.
- Router registration errors should be logged and cause only that feature to be skipped, not whole-app failure.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The project MUST provide a minimal project layout with `core/`, `apps/`, and a top-level `main.py` entrypoint.
- **FR-002**: `apps/mqtt_worker.client` MUST expose an async function `start_mqtt_loop()` that runs until cancelled and handles `asyncio.CancelledError` for graceful shutdown.
- **FR-003**: `main.py` MUST attempt to import feature modules (`apps.mqtt_worker.client`, `apps.api_server.routers`) inside `try/except ImportError` blocks and skip missing modules without failing startup.
- **FR-004**: Background workers MUST be launched via `asyncio.create_task()` inside FastAPI's lifespan context and MUST be cancelled/awaited on shutdown.
- **FR-005**: `apps.api_server.routers` MUST expose a `router: APIRouter` and, when present, be mounted at the `/api/v1` prefix.
- **FR-006**: The application MUST expose GET `/health` that returns a small JSON status payload for liveness checks.
- **FR-007**: Runtime logging MUST use Python's `logging` module and include lifecycle events: "LOAD SUCCESS", "LOAD SKIPPED", "SHUTDOWN".

*Notes:* These requirements are intentionally specific because the user requested a concrete FastAPI-based boilerplate implementation; assumptions are documented below.

### Key Entities *(include if feature involves data)*

- **PresignedURL**: Represents a short-lived upload URL issued to clients. Key attributes: `url: string`, `status: string`.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: The application starts successfully and responds to GET `/health` within 2 seconds when run on a developer machine with any subset of `apps/` present.
- **SC-002**: When `apps/api_server` is present, GET `/api/v1/presigned-url` returns a JSON payload containing both `url` and `status` with `status == "ok"` for 100% of test requests.
- **SC-003**: When `apps/mqtt_worker` is present, cancelling the application (SIGINT/SIGTERM) results in the worker's cancellation and process exit within 10 seconds; logs must indicate cancellation and clean shutdown.
- **SC-004**: No `print()` statements appear in runtime code; logging uses the `logging` module and includes lifecycle events.

## Assumptions

- This feature will be implemented in Python 3.10+ and uses FastAPI for the HTTP surface (per user request and repository constitution).
- The presigned URL endpoint is a placeholder and does not attempt to integrate with external storage services in this POC.
- Developers have a normal Python development environment (venv, pip) and can run `uvicorn main:app` to start the server.

## Acceptance Tests (how to validate)

1. Start the app with all apps present: `uvicorn main:app --reload` and verify `/health` and `/api/v1/presigned-url` behave as specified.
2. Rename or remove `apps/api_server` and restart; verify `/health` still returns OK and `/api/v1/presigned-url` returns 404 or is not registered.
3. Start the app with `apps/mqtt_worker` present, then stop the process; confirm logs show worker cancellation and the process exits within 10 seconds.

---

No [NEEDS CLARIFICATION] markers remain.
