from pydantic import BaseModel, field_validator
from typing import Literal

class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message content must not be blank")
        return v

class AssistantRequest(BaseModel):
    prompt: str
    history: list[ConversationMessage] = []

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Prompt must not be blank")
        if len(v) > 2000:
            raise ValueError("Prompt must not exceed 2000 characters")
        return v

    @field_validator("history")
    @classmethod
    def trim_history(cls, v: list) -> list:
        return v[-20:]

class AssistantResponse(BaseModel):
    reply: str
    issues_modified: bool