import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.api.v1.routes import router
from app.utils.logging import setup_logging

logger = setup_logging()

app = FastAPI(title=settings.APP_NAME, version="1.0.0")
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": settings.APP_NAME, "status": "running"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=settings.DEBUG)
