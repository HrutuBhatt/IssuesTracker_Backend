from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repository.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectMemberAdd
from app.models.models import Project, ProjectMember, ProjectRole


class ProjectService:
    def __init__(self, db: Session):
        self.repo = ProjectRepository(db)

    def create_project(self, payload: ProjectCreate, creator_id: int) -> Project:
        # 1. Create the project
        project = self.repo.create(
            name=payload.name,
            description=payload.description,
            created_by=creator_id
        )
        # 2. Automatically add creator as ADMIN
        self.repo.add_member(
            project_id=project.id,
            user_id=creator_id,
            role=ProjectRole.ADMIN,
            invited_by=creator_id
        )
        return project

    def get_projects_for_user(self, user_id: int) -> list[Project]:
        return self.repo.get_projects_for_user(user_id)

    def get_project_by_id(self, project_id: int, user_id: int) -> Project:
        # Check membership
        member = self.repo.get_member(project_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project."
            )
        project = self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found."
            )
        project.role = member.role
        return project

    def add_project_member(self, project_id: int, payload: ProjectMemberAdd, inviter_id: int) -> ProjectMember:
        # Check if inviter is an admin of this project
        inviter_member = self.repo.get_member(project_id, inviter_id)
        if not inviter_member or inviter_member.role != ProjectRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project admins can invite members."
            )
        
        return self.repo.add_member(
            project_id=project_id,
            user_id=payload.user_id,
            role=payload.role,
            invited_by=inviter_id
        )

    def get_members(self, project_id: int, user_id: int) -> list[ProjectMember]:
        # Validate that the user asking is a member of the project
        member = self.repo.get_member(project_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to view this project's members."
            )
        return self.repo.get_members_for_project(project_id)

    def update_member_role(self, project_id: int, member_user_id: int, role: ProjectRole, actor_id: int) -> ProjectMember:
        # Validate that actor is admin of the project
        actor_member = self.repo.get_member(project_id, actor_id)
        if not actor_member or actor_member.role != ProjectRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project admins can modify member roles."
            )
        
        # Don't let an admin change their own role (prevent lockouts)
        if member_user_id == actor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role."
            )
            
        return self.repo.update_member_role(project_id, member_user_id, role)

    def remove_member(self, project_id: int, member_user_id: int, actor_id: int) -> None:
        # Validate actor is admin
        actor_member = self.repo.get_member(project_id, actor_id)
        if not actor_member or actor_member.role != ProjectRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project admins can remove members."
            )
            
        # Don't let an admin remove themselves
        if member_user_id == actor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove yourself from the project."
            )
            
        self.repo.remove_member(project_id, member_user_id)

    def delete_project(self, project_id: int, actor_id: int) -> None:
        member = self.repo.get_member(project_id, actor_id)
        if not member or member.role != ProjectRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project admins can delete the project."
            )
        self.repo.delete(project_id)
