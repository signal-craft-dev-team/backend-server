# <!--
Sync Impact Report
- Version change: TEMPLATE/UNSET -> 0.1.0
- Modified principles:
  - PRINCIPLE_1_NAME (template placeholder) -> Graceful Degradation (선택적 로드)
  - PRINCIPLE_2_NAME (template placeholder) -> Modular Apps & Core Separation
  - PRINCIPLE_3_NAME (template placeholder) -> Async-First Lifespan Workers
  - PRINCIPLE_4_NAME (template placeholder) -> Structured Logging & Observability
  - PRINCIPLE_5_NAME (template placeholder) -> Routing & API Versioning
- Added sections:
  - Architecture Overview
  - Technology Stack & Conventions
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ updated
  - .specify/templates/spec-template.md ✅ reviewed
  - .specify/templates/tasks-template.md ✅ reviewed
- Follow-up TODOs:
  - None
-->

# Edge Sound AI Backend Monorepo Constitution

## Core Principles

### Graceful Degradation (선택적 로드)
- The system MUST support local development patterns such as git sparse-checkout. Missing feature modules under `apps/` MUST NOT cause the main server to crash.
- `main.py` (or the application entrypoint) MUST import feature modules inside a `try/except ImportError` block and continue startup when a module is absent.
- When an ImportError is caught, the system MUST log the event at INFO or WARNING level as "LOAD SKIPPED: <app_name>" including the reason.
- Feature absence MUST be treated as a disabled feature (no side effects), not an error state.

### Modular Apps & Core Separation
- All feature code MUST live under `apps/` as independently deployable/testable modules; shared/common utilities belong in `core/`.
- Each app module MUST be self-contained (models, services, API router or registration hook) and MUST declare required runtime hooks rather than importing other apps at module import time.
- Cross-app runtime dependencies are STRONGLY DISCOURAGED; when necessary they MUST be explicit and documented.

### Async-First Lifespan Workers
- Asynchronous I/O (`asyncio`) is the default concurrency model. Blocking operations MUST be run in appropriate thread executors.
- Background workers MUST be created inside FastAPI's `lifespan` using `asyncio.create_task()` and MUST be cleanly cancelled and awaited on shutdown.
- Worker lifecycle must be deterministic and failure modes must be logged.

### Structured Logging & Observability
- `print()` is PROHIBITED in the runtime code. All runtime diagnostics MUST use Python's `logging` module.
- Logs MUST include clear, machine-parseable statuses for lifecycle events: "LOAD SUCCESS", "LOAD SKIPPED", "SHUTDOWN".
- Production deployments SHOULD use structured (e.g., JSON) logs and include app/module identifiers and correlation ids where applicable.

### Routing & API Versioning
- The HTTP API surface exposed by feature modules MUST be mounted under the `/api/v1` prefix by the main application.
- Feature routers MUST be defined as FastAPI `APIRouter` instances (commonly named `router`) or expose a `register(app: FastAPI)` function to perform registration.
- Public API changes MUST follow semantic versioning and include a migration plan for breaking changes.

## Technology Stack & Conventions
- Framework: FastAPI on Python 3.10 or later.
- Concurrency: Use `asyncio` for non-blocking I/O; prefer `async def` endpoints and services.
- Background workers: Start inside FastAPI `lifespan` with `asyncio.create_task()` and cancel on shutdown.
- Logging: Use Python's `logging` module; no `print()` calls; prefer structured logs for production.
- Routing: All routers mounted beneath `/api/v1`.
- Linting & Quality: Projects SHOULD use linters (e.g., `ruff`, `flake8`) and formatters (e.g., `black`) and run pre-commit checks where possible.

## Architecture Overview
- This repository is a monorepo managing multiple backend features for the Edge Sound AI system.
- Feature modules live under `apps/` and are intended to be independently developed and optionally checked out (sparse-checkout).
- Shared logic and utilities live in `core/`.
- The main server entrypoint (`main.py`) MUST attempt to import and register each app safely; missing apps are skipped without failure.

## Governance
- Amendments: Changes to this constitution MUST be proposed as a PR that includes:
	- A clear description of the change and rationale.
	- A migration/compatibility plan for any breaking changes.
	- At least one approving review from a project maintainer or owner.
- Versioning: Constitution uses semantic versioning. MAJOR for breaking governance changes, MINOR for added principles/sections, PATCH for wording/typo fixes.
- Compliance: Plans and implementation templates MUST include a "Constitution Check" gate (see `.specify/templates/plan-template.md`) to validate compliance during planning.
- Review cadence: This constitution SHOULD be reviewed at least annually or when a major architecture change is proposed.

**Version**: 0.1.0 | **Ratified**: 2026-03-18 | **Last Amended**: 2026-03-18

