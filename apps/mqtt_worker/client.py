import asyncio
import logging

logger = logging.getLogger(__name__)


async def start_mqtt_loop() -> None:
    """Simulated MQTT listener loop.

    Runs until cancelled. Uses an interval to simulate message polling and
    handles asyncio.CancelledError to perform graceful shutdown.
    """
    logger.info("MQTT worker: start_mqtt_loop started")
    try:
        while True:
            # Simulate receiving a diagnostic signal from devices
            logger.info("MQTT worker: listening for device diagnostics...")
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        logger.info("MQTT worker: cancellation received, cleaning up")
        # perform cleanup here if needed
    finally:
        logger.info("MQTT worker: exiting")
