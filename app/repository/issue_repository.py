from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Issue
from app.schemas.issue import IssueCreate, IssueUpdate


class IssueRepository:
    """Handles all database operations for the Issue model."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Issue]:
        """Fetch all non-deleted issues."""
        return self.db.query(Issue).filter(Issue.deleted_at.is_(None)).all()

    def get_by_id(self, issue_id: int) -> Issue | None:
        """Fetch a single non-deleted issue by ID. Returns None if not found."""
        return self.db.query(Issue).filter(
            Issue.id == issue_id,
            Issue.deleted_at.is_(None)
        ).first()

    def create(self, data: IssueCreate) -> Issue:
        """Create and persist a new issue."""
        issue = Issue(**data.model_dump())
        self.db.add(issue)
        try:
            self.db.commit()
            self.db.refresh(issue)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create issue.",
            ) from e
        return issue

    def update(self, issue: Issue, data: IssueUpdate) -> Issue:
        """Update only the fields the client provided."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(issue, field, value)
        # updated_at is handled automatically by SQLAlchemy's onupdate
        try:
            self.db.commit()
            self.db.refresh(issue)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update issue.",
            ) from e
        return issue

    def delete(self, issue: Issue) -> None:
        """Soft-delete an issue by setting deleted_at timestamp."""
        issue.deleted_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete issue.",
            ) from e
