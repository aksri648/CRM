from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Xeno Agent Service"
    DEBUG: bool = True
    APP_SERVICE_URL: str = "http://app-service:8001"

    REDIS_URL: str = ""
    RQ_QUEUE_NAME: str = "agent-jobs"
    RQ_ENABLED: bool = False
    RQ_JOB_TIMEOUT: int = 300

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    LLM_ENABLED: bool = False
    LLM_TIMEOUT_SECONDS: int = 30

    # Deterministic NLP segment classifier. ON by default — pure-Python, no
    # external deps, only improves Atlas's fallback path. Disable to test
    # the legacy keyword-match path.
    NLP_CLASSIFIER_ENABLED: bool = True
    # Minimum classifier confidence required to override the LLM segment when
    # the two disagree. Below this, the LLM's choice wins.
    NLP_OVERRIDE_THRESHOLD: float = 0.75

    class Config:
        env_file = ".env"


settings = Settings()
