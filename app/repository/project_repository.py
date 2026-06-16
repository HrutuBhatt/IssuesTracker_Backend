from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.models.models import Project, ProjectMember, ProjectRole


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, description: str | None, created_by: int) -> Project:
        project = Project(name=name, description=description, created_by=created_by)
        self.db.add(project)
        try:
            self.db.commit()
            self.db.refresh(project)
            return project
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project."
            )

    def get_by_id(self, project_id: int) -> Project | None:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_projects_for_user(self, user_id: int) -> list[Project]:
        # Fetch all projects where user is a member
        memberships = self.db.query(ProjectMember).filter(ProjectMember.user_id == user_id).all()
        project_ids = [m.project_id for m in memberships]
        
        # Also include projects created by the user just in case, though they should be a member anyway
        return self.db.query(Project).filter(
            (Project.id.in_(project_ids)) | (Project.created_by == user_id)
        ).all()

    def add_member(self, project_id: int, user_id: int, role: ProjectRole, invited_by: int) -> ProjectMember:
        # Check if already a member
        existing = self.get_member(project_id, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this project."
            )

        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by
        )
        self.db.add(member)
        try:
            self.db.commit()
            self.db.refresh(member)
            return member
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add project member."
            )

    def get_member(self, project_id: int, user_id: int) -> ProjectMember | None:
        return self.db.query(ProjectMember).options(joinedload(ProjectMember.user)).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()

    #get all the members of the project
    def get_members_for_project(self, project_id: int) -> list[ProjectMember]:
        return self.db.query(ProjectMember).options(joinedload(ProjectMember.user)).filter(
            ProjectMember.project_id == project_id
        ).all()

    def update_member_role(self, project_id: int, user_id: int, role: ProjectRole) -> ProjectMember:
        member = self.get_member(project_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project member not found."
            )
        member.role = role
        try:
            self.db.commit()
            self.db.refresh(member)
            return member
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update member role."
            )

    def remove_member(self, project_id: int, user_id: int) -> None:
        member = self.get_member(project_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project member not found."
            )
        self.db.delete(member)
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member."
            )

    def delete(self, project_id: int) -> None:
        project = self.get_by_id(project_id)
        if project:
            self.db.delete(project)
            try:
                self.db.commit()
            except SQLAlchemyError as e:
                self.db.rollback()
                print(f"DATABASE ERROR ON DELETING PROJECT: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete project: {str(e)}"
                )
