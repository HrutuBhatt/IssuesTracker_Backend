from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.models import Issue, IssueHistory
from app.schemas.issue import IssueCreate, IssueUpdate


class IssueRepository:
    """Handles all database operations for the Issue model."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_for_project(self, project_id: int) -> list[Issue]:
        """Fetch all non-deleted issues for a specific project."""
        return self.db.query(Issue).filter(
            Issue.project_id == project_id,
            Issue.deleted_at.is_(None)
        ).all()

    def get_by_id(self, issue_id: int) -> Issue | None:
        """Fetch a single non-deleted issue by ID. Returns None if not found."""
        return self.db.query(Issue).filter(
            Issue.id == issue_id,
            Issue.deleted_at.is_(None)
        ).first()

    def create(self, project_id: int, creator_id: int, data: IssueCreate) -> Issue:
        """Create and persist a new issue."""
        issue = Issue(
            project_id=project_id,
            created_by=creator_id,
            **data.model_dump()
        )
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

    def add_history_entry(
        self,
        issue_id: int,
        changed_by: int,
        field_changed: str,
        old_value: str | None,
        new_value: str | None
    ) -> None:
        """Insert a change history record."""
        entry = IssueHistory(
            issue_id=issue_id,
            changed_by=changed_by,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value
        )
        self.db.add(entry)
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            # We log history errors but don't break the application flow
            print(f"[Warning] Failed to write issue history: {e}")

    def get_history(self, issue_id: int) -> list[IssueHistory]:
        """Fetch audit log for a specific issue ordered by date descending."""
        return self.db.query(IssueHistory).filter(
            IssueHistory.issue_id == issue_id
        ).order_by(IssueHistory.changed_at.desc()).all()
