from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import Issue, IssueHistory
from app.repository.issue_repository import IssueRepository
from app.schemas.issue import IssueCreate, IssueUpdate


class IssueService:
    """Business logic layer for Issue operations."""

    def __init__(self, db: Session):
        self.repo = IssueRepository(db)

    def get_all_issues(self, project_id: int) -> list[Issue]:
        """Return all issues for a project."""
        return self.repo.get_all_for_project(project_id)

    def get_issue_by_id(self, issue_id: int) -> Issue:
        """Return a single issue, or raise 404 if not found."""
        issue = self.repo.get_by_id(issue_id)
        if issue is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with id {issue_id} not found",
            )
        return issue

    def create_issue(self, project_id: int, creator_id: int, data: IssueCreate) -> Issue:
        """Create and return a new issue."""
        return self.repo.create(project_id, creator_id, data)

    def update_issue(self, issue_id: int, data: IssueUpdate, actor_id: int) -> Issue:
        """Update an existing issue and audit the changes in history."""
        issue = self.get_issue_by_id(issue_id)

        # Audit history tracking
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            old_val = getattr(issue, field)
            
            # Stringify values for audit log (handling Enums/None/Int)
            old_val_str = str(old_val.value) if hasattr(old_val, 'value') else (str(old_val) if old_val is not None else None)
            new_val_str = str(value.value) if hasattr(value, 'value') else (str(value) if value is not None else None)
            
            if old_val_str != new_val_str:
                self.repo.add_history_entry(
                    issue_id=issue_id,
                    changed_by=actor_id,
                    field_changed=field,
                    old_value=old_val_str,
                    new_value=new_val_str
                )

        return self.repo.update(issue, data)

    def delete_issue(self, issue_id: int) -> None:
        """Delete an issue. Raises 404 if issue doesn't exist."""
        issue = self.get_issue_by_id(issue_id)
        self.repo.delete(issue)

    def get_issue_history(self, issue_id: int) -> list[IssueHistory]:
        """Fetch audit log for a specific issue."""
        # Check if issue exists
        self.get_issue_by_id(issue_id)
        return self.repo.get_history(issue_id)
