from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import IssueStatus


class IssueBase(BaseModel):
    """Shared fields between Create and Response."""
    title: str
    description: str | None = None
    status: IssueStatus = IssueStatus.OPEN

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be blank")
        return v.strip()


class IssueCreate(IssueBase):
    """Schema for POST /issues — title is required."""
    pass


class IssueUpdate(BaseModel):
    """Schema for PUT /issues/<id> — all fields optional."""
    title: str | None = None
    description: str | None = None
    status: IssueStatus | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Title must not be blank")
        return v.strip() if v else v


class IssueResponse(IssueBase):
    """Schema for API responses — includes DB-generated fields."""
    id: int
    created_at: datetime
    updated_at: datetime | None = None 

    model_config = ConfigDict(from_attributes=True)  # reads SQLAlchemy model attrs
