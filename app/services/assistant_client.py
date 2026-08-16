from functools import lru_cache
from groq import Groq

from app.core.config import settings


class AssistantClient:
    """Stateless Groq client — lives for app lifetime."""

    def __init__(self):
        self.groq = Groq(api_key=settings.GROQ_API_KEY)


@lru_cache()
def get_assistant_client() -> AssistantClient:
    return AssistantClient()
