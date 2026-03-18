# research.md

## Decisions

- Decision: Use FastAPI on Python 3.10+ for the HTTP surface.
  - Rationale: FastAPI provides an async-first framework, clear router semantics, and Pydantic for data validation. It is lightweight and well-suited for small services and POCs.
  - Alternatives considered: Flask (synchronous by default), Starlette (lower-level), aiohttp (async but less batteries-included). Rejected due to slower iteration or missing validation ergonomics.

- Decision: Use `asyncio` for background worker concurrency and start workers inside FastAPI `lifespan`.
  - Rationale: `asyncio` is part of the standard library, matches FastAPI's async model, and keeps the POC simple (no external queue/worker infra).
  - Alternatives considered: Celery or dedicated background process — heavier weight and requires infra (broker), not necessary for this POC.

- Decision: Logging via Python's `logging` and structured messages (plain JSON optional later).
  - Rationale: Constitution requires no `print()`; `logging` is standard and integrates with most hosting platforms. If structured logs are needed, adopt `structlog` or a JSON formatter.

- Decision: Presigned URL endpoint returns a dummy URL for POC.
  - Rationale: External storage integration (S3, GCS) is out of scope for the POC; the endpoint contract is the important artifact.

## Alternatives and trade-offs

- Using a separate worker process (systemd/container) would provide isolation but increases complexity for testing and local development. The in-process `lifespan` worker is simpler and adequate to validate lifecycle semantics.

- Using Flask plus gevent/threading could support async behavior but reduces type-safety and will require more plumbing for background tasks.

## Actionable outcome

- Implement FastAPI-based POC (done).  
- Keep design modular so later migration to an out-of-process worker or adding real presigned URL generation is straightforward.
