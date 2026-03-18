# data-model.md

## Entities

- **PresignedURL**
  - Fields:
    - `url: string` — the upload endpoint the client should use (POC: dummy URL)
    - `status: string` — e.g., `ok` or `error`
    - `expires_at: datetime | null` — optional expiry for real signed URLs
  - Validation: `url` must be a non-empty string; `status` must be one of `ok` or `error`.
  - Notes: This POC does not persist URLs; generation is ephemeral.

## Worker state

- The MQTT worker is a streaming/ephemeral process that does not maintain a persistent data model in this POC. Any needed events should be emitted to logs or a future events table in a long-term design.
