"""Application entrypoint with graceful, sparse-checkout-friendly startup.

This module follows the repository constitution: feature imports are attempted
inside try/except ImportError blocks so missing apps do not prevent startup.
Background workers are created inside FastAPI's lifespan and cancelled on shutdown.
"""
import logging
from contextlib import asynccontextmanager
import asyncio
from typing import Any
from fastapi import FastAPI


logger = logging.getLogger("signal_craft_backend_server")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    bg_task = None

    # Attempt to import and start MQTT worker. If missing, skip gracefully.
    try:
        from apps.mqtt_worker.client import start_mqtt_loop
    except ImportError as e:
        start_mqtt_loop = None
        logger.info(f"LOAD SKIPPED: mqtt_worker ({e})")
    else:
        try:
            bg_task = asyncio.create_task(start_mqtt_loop())
            logger.info("LOAD SUCCESS: mqtt_worker started")
        except Exception as e:
            logger.info(f"LOAD SKIPPED: mqtt_worker (failed to start: {e})")
            bg_task = None

    # Attempt to import API router and register it under /api/v1 if present
    try:
        from apps.api_server.routers import router as api_router
    except ImportError as e:
        api_router = None
        logger.info(f"LOAD SKIPPED: api_server ({e})")
    else:
        try:
            app.include_router(api_router, prefix="/api/v1")
            logger.info("LOAD SUCCESS: api_server router included at /api/v1")
        except Exception as e:
            logger.info(f"LOAD SKIPPED: api_server (failed to include router: {e})")

    try:
        yield
    finally:
        # Cancel background worker if it was started
        if bg_task is not None:
            logger.info("SHUTTING DOWN: cancelling mqtt_worker")
            bg_task.cancel()
            try:
                await asyncio.wait_for(bg_task, timeout=10)
            except asyncio.CancelledError:
                logger.info("SHUTDOWN: mqtt_worker cancelled")
            except Exception as e:
                logger.info(f"SHUTDOWN: mqtt_worker error during cancellation: {e}")
        logger.info("SHUTDOWN: application")


app = FastAPI(lifespan=lifespan, title="SignalCraft Backend Server", version="1.0.1")


@app.get("/health")
async def health():
    return {"status": "ok"}
