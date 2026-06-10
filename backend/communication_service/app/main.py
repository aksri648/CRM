import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.routes import router
from app.database import create_tables, async_session
from app.utils.logging import setup_logging
from app.workers.queue_processor import QueueProcessor

logger = setup_logging()


async def _queue_worker_loop():
    while True:
        try:
            async with async_session() as session:
                processor = QueueProcessor(session)
                processed = await processor.process_batch()
                if processed == 0:
                    await asyncio.sleep(2)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("queue_worker_error", error=str(exc))
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("communication_service_starting")
    await create_tables()
    worker_task = asyncio.create_task(_queue_worker_loop())
    try:
        yield
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": settings.APP_NAME, "status": "running"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=settings.DEBUG)
