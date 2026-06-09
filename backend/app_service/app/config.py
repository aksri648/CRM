import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Xeno App Service"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://xeno:xeno@localhost:5432/xeno"

    JWT_SECRET_KEY: str = "super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    AGENT_SERVICE_URL: str = "http://agent-service:8002"
    COMMUNICATION_SERVICE_URL: str = "http://communication-service:8003"

    class Config:
        env_file = ".env"


settings = Settings()
