# Quickstart — Boilerplate Implementation

1. Create and activate a Python 3.10+ virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install fastapi uvicorn
# For tests / linting (optional):
pip install pytest ruff black
```

3. Run the app locally:

```bash
uvicorn main:app --reload
```

4. Verify endpoints:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/api/v1/uploads/presign \
	-H 'Content-Type: application/json' \
	-d '{
		"device_id": "DCB4D91BAD48",
		"sequence": 1,
		"timestamp_ms": 1710840000000,
		"file_name": "device_DCB4D91BAD48_03E771F4B2B77CCA_seq_1.wav",
		"content_type": "audio/wav",
		"byte_length": 123456
	}'
```

The resulting object path should follow the device layout:
`gs://device-raw-data/raw-audio/DCB4D91BAD48/device_DCB4D91BAD48_03E771F4B2B77CCA_seq_1.wav`

5. Sparse-checkout validation:

- Remove or rename `apps/api_server` or `apps/mqtt_worker` and restart the server; the app should still start and `/health` should return `{"status":"ok"}`.
