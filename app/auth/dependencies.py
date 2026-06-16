from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, ProjectMember, ProjectRole, Issue
from app.auth.utils import decode_token


bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    user_id = decode_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def require_project_membership(allowed_roles: list[ProjectRole]):
    def dependency(
        project_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> ProjectMember:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()

        if not member or member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have permission to access this project."
            )
        return member
    return dependency


def require_issue_permission(allowed_roles: list[ProjectRole]):
    def dependency(
        issue_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> Issue:
        issue = db.query(Issue).filter(
            Issue.id == issue_id,
            Issue.deleted_at.is_(None)
        ).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found."
            )

        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == issue.project_id,
            ProjectMember.user_id == current_user.id
        ).first()

        if not member or member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have permission to access this issue."
            )
        return issue
    return dependency