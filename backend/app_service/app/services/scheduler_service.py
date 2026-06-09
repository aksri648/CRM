from app.utils.logging import logger


async def run_analytics_refresh():
    logger.info("scheduler_analytics_refresh_started")
    try:
        from app.services.analytics_service import invalidate_analytics_cache
        await invalidate_analytics_cache()
        logger.info("scheduler_analytics_refresh_completed")
    except Exception as e:
        logger.error("scheduler_analytics_refresh_failed", error=str(e))
