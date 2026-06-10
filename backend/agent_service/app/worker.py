"""RQ worker entry point.

Usage (locally):
    python -m app.worker

Render Background Worker start command:
    python -m app.worker

Reads REDIS_URL and RQ_QUEUE_NAME from environment via app.config.settings.
"""
from rq import Worker
from app.config import settings
from app.jobs.queue import get_queue, get_redis
from app.utils.logging import setup_logging


def main() -> None:
    logger = setup_logging()
    if not settings.REDIS_URL:
        logger.error("redis_url_missing")
        raise SystemExit("REDIS_URL is required to start the RQ worker")
    queue = get_queue()
    logger.info("rq_worker_starting", queue=settings.RQ_QUEUE_NAME, redis=settings.REDIS_URL[:30] + "…")
    Worker([queue], connection=get_redis()).work(with_scheduler=False)


if __name__ == "__main__":
    main()
