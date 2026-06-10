"""Groq LLM client factory.

All agents that opt into LLM inference go through this module. Lazy-cached
per (temperature, model) so we don't reinstantiate the client every call.
"""
from functools import lru_cache
from typing import Any

from app.config import settings


def llm_available() -> bool:
    """Cheap gate — agents call this before attempting structured-output calls."""
    return bool(settings.LLM_ENABLED and settings.GROQ_API_KEY)


@lru_cache(maxsize=8)
def _make_llm(temperature: float, model: str) -> Any:
    from langchain_groq import ChatGroq
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=model,
        temperature=temperature,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=2,
    )


def get_llm(temperature: float = 0.2, model: str | None = None) -> Any:
    return _make_llm(temperature, model or settings.GROQ_MODEL)
