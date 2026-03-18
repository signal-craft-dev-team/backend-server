from fastapi import APIRouter

router = APIRouter()


@router.get("/presigned-url")
async def presigned_url():
    """Return a dummy presigned URL and status for clients.

    This is a placeholder endpoint for the POC.
    """
    return {"url": "https://example.com/presigned/object", "status": "ok"}
