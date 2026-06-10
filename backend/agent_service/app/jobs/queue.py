from functools import lru_cache
from redis import Redis
from rq import Queue
from app.config import settings


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    if not settings.REDIS_URL:
        raise RuntimeError("REDIS_URL is not configured")
    return Redis.from_url(settings.REDIS_URL)


@lru_cache(maxsize=1)
def get_queue() -> Queue:
    return Queue(settings.RQ_QUEUE_NAME, connection=get_redis(), default_timeout=settings.RQ_JOB_TIMEOUT)
