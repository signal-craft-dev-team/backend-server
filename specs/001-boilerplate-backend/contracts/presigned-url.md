# Contract: POST /api/v1/uploads/presign

**Endpoint**: `POST /api/v1/uploads/presign`

**Description**: Returns a presigned URL for client uploads (POC returns a dummy URL).

**Request**:

- Method: POST
- Path: `/api/v1/uploads/presign`
- Body: JSON object with `device_id`, `sequence`, `timestamp_ms`, `file_name`, `content_type`, `byte_length`
- Auth: none (POC)

**Response (200)**:

```json
{
  "url": "https://example.com/presigned/object",
  "status": "ok"
}
```

**Errors**:

- 500: `{ "status": "error", "message": "internal error" }`

**Notes**:

- In production, this endpoint should validate client permissions and generate time-limited URLs against a storage provider (S3, GCS). Authentication and rate-limiting should be added.
