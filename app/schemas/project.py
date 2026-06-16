from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.models import ProjectRole


class ProjectBase(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project name must not be blank")
        return v.strip()


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    created_by: int
    created_at: datetime
    role: ProjectRole | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberAdd(BaseModel):
    user_id: int
    role: ProjectRole = ProjectRole.CLIENT


class ProjectMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    email: str
    role: ProjectRole
    invited_by: int | None = None
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
