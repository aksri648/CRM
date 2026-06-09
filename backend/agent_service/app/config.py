from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Xeno Agent Service"
    DEBUG: bool = True
    APP_SERVICE_URL: str = "http://app-service:8001"

    class Config:
        env_file = ".env"


settings = Settings()
