from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import User, ProjectRole, ProjectMember
from app.auth.dependencies import get_current_user, require_project_membership
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectMemberAdd,
    ProjectMemberResponse
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ProjectService(db)
    return service.create_project(payload, current_user.id)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ProjectService(db)
    return service.get_projects_for_user(current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # This also enforces project access validation
    service = ProjectService(db)
    return service.get_project_by_id(project_id, current_user.id)


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    project_id: int,
    payload: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_admin: ProjectMember = Depends(require_project_membership([ProjectRole.ADMIN]))
):
    service = ProjectService(db)
    return service.add_project_member(project_id, payload, current_admin.user_id)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def get_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_member: ProjectMember = Depends(require_project_membership([ProjectRole.ADMIN, ProjectRole.DEVELOPER, ProjectRole.CLIENT]))
):
    service = ProjectService(db)
    return service.get_members(project_id, current_member.user_id)


@router.put("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
def update_member_role(
    project_id: int,
    user_id: int,
    role: ProjectRole = Query(...),
    db: Session = Depends(get_db),
    current_admin: ProjectMember = Depends(require_project_membership([ProjectRole.ADMIN]))
):
    service = ProjectService(db)
    return service.update_member_role(project_id, user_id, role, current_admin.user_id)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: ProjectMember = Depends(require_project_membership([ProjectRole.ADMIN]))
):
    service = ProjectService(db)
    service.remove_member(project_id, user_id, current_admin.user_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_admin: ProjectMember = Depends(require_project_membership([ProjectRole.ADMIN]))
):
    service = ProjectService(db)
    service.delete_project(project_id, current_admin.user_id)
