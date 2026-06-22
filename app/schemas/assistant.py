from pydantic import BaseModel, field_validator

class AssistantRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Prompt must not be blank")
        if len(v) > 2000:
            raise ValueError("Prompt must not exceed 2000 characters")
        return v


class AssistantResponse(BaseModel):
    reply: str
    issues_modified: bool