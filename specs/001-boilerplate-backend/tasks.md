---
description: "Task list for Boilerplate Implementation"
---

# Tasks: Boilerplate Implementation

**Input**: Design documents from `/specs/001-boilerplate-backend/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create package layout and placeholders: add `core/__init__.py`, `apps/__init__.py`, `apps/api_server/__init__.py`, `apps/mqtt_worker/__init__.py`
- [x] T002 Initialize runtime dependencies in `requirements.txt` (add `fastapi`, `uvicorn`)
- [x] T003 [P] Add development dependencies to `requirements-dev.txt` (add `pytest`, `pytest-asyncio`, `ruff`, `black`)
- [x] T004 Create Quickstart document at `specs/001-boilerplate-backend/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T005 Implement application entrypoint with lifespan and sparse-checkout tolerant imports: `main.py`
- [ ] T006 [P] Add centralized logging helper in `core/logging.py` and update modules to use it
- [ ] T007 [P] Ensure API router export convention: `apps/api_server/routers.py` exposes `router`
- [ ] T008 Create service contract file: `specs/001-boilerplate-backend/contracts/presigned-url.md`
- [ ] T009 [P] Add data model documentation: `specs/001-boilerplate-backend/data-model.md`

**Checkpoint**: Foundational items must be complete before user stories.

---

## Phase 3: User Story 1 - Run reliably with missing feature modules (Priority: P1) 🎯 MVP

**Goal**: Server starts and responds to health checks even when some `apps/` submodules are absent.

- [ ] T010 [US1] Implement GET `/health` in `main.py` returning `{ "status": "ok" }`
- [ ] T011 [US1] Add integration test for health endpoint: `tests/integration/test_health.py` (use FastAPI `TestClient` or `pytest-asyncio`)
- [ ] T012 [US1] Add sparse-checkout validation script: `scripts/validate_sparse_checkout.sh` documenting manual steps and checks (or automated sanity test under `tests/integration/test_sparse_checkout.py`)

**Independent Test**: Run `pytest tests/integration/test_health.py` (or `uvicorn main:app` + `curl /health`) — must pass even if `apps/api_server` or `apps/mqtt_worker` are removed.

---

## Phase 4: User Story 2 - Issue presigned URLs (Priority: P2)

**Goal**: Provide a presigned URL endpoint for clients (POC returns a dummy URL).

- [ ] T013 [US2] Implement GET `/api/v1/presigned-url` in `apps/api_server/routers.py` (ensure router is exported)
- [ ] T014 [US2] Add contract test: `tests/contract/test_presigned_url_contract.py` to validate response matches `specs/001-boilerplate-backend/contracts/presigned-url.md`
- [ ] T015 [US2] Add integration test for endpoint: `tests/integration/test_presigned_url.py` asserting JSON contains keys `url` and `status` with `status == "ok"`

---

## Phase 5: User Story 3 - Background MQTT worker lifecycle (Priority: P3)

**Goal**: Run an in-process MQTT-listener-style worker that is cancelled cleanly on shutdown.

- [ ] T016 [US3] Implement `start_mqtt_loop()` in `apps/mqtt_worker/client.py` to run until cancelled and log lifecycle events
 - [x] T016 [US3] Implement `start_mqtt_loop()` in `apps/mqtt_worker/client.py` to run until cancelled and log lifecycle events
- [ ] T017 [US3] Add asyncio-based integration test: `tests/integration/test_mqtt_worker_lifecycle.py` that starts `start_mqtt_loop()` as a task, cancels it, and asserts clean shutdown (use `pytest-asyncio`)
- [ ] T018 [US3] Add worker README at `apps/mqtt_worker/README.md` describing expected behavior and configuration

---

## Phase N: Polish & Cross-Cutting Concerns

- [ ] T019 [P] Run linters and fix style: target files `main.py`, `apps/`, `core/` (command: `ruff check main.py apps/ core/`)
- [ ] T020 [P] Add CI workflow to run `pytest` and `ruff` on push: `.github/workflows/ci.yml`
- [ ] T021 [P] Update repository `README.md` with quickstart and run instructions (add `README.md` at repo root)
- [ ] T022 [P] Add pre-commit configuration `.pre-commit-config.yaml` for `ruff` and `black`
- [ ] T023 Commit changes to branch `001-boilerplate-backend` and open a PR for review

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: No dependencies — start here
- **Foundational (Phase 2)**: Blocks all user stories
- **User Stories (Phase 3+)**: Depend on Foundational completion; each User Story is independently testable

## Parallel Opportunities

- Linting, dev-deps installation, quickstart doc, and CI config tasks (`[P]`) can be done in parallel with implementation tasks after foundational items are complete.

## Implementation Strategy

1. Complete Phase 1 (T001–T004) to establish environment and docs.
2. Complete Phase 2 (T005–T009). STOP and validate `main.py` startup behavior and Constitution Check.
3. Implement User Story 1 (T010–T012) as MVP and validate independently.
4. Implement User Story 2 and 3 in priority order or in parallel depending on team capacity.
5. Add CI, linting, and docs (Phase N) and open PR.
