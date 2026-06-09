from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Xeno Communication Service"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://xeno:xeno@localhost:5432/xeno"
    APP_SERVICE_URL: str = "http://app-service:8001"
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: int = 60
    DLQ_MAX_SIZE: int = 10000
    BATCH_SIZE: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
