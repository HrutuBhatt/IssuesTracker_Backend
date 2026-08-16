from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.models import IssueStatus, IssuePriority, IssueType


class IssueBase(BaseModel):
    title: str
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be blank")
        return v.strip()
        

class IssueCreate(IssueBase):
    priority: IssuePriority
    issue_type: IssueType
    assigned_to: int | None = None


class IssueUpdate(IssueBase):
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    issue_type: IssueType | None = None
    assigned_to: int | None = None


class IssueResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None = None
    status: IssueStatus
    priority: IssuePriority
    issue_type: IssueType
    created_by: int
    assigned_to: int | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class IssueHistoryResponse(BaseModel):
    id: int
    issue_id: int
    changed_by: int
    field_changed: str
    old_value: str | None = None
    new_value: str | None = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
