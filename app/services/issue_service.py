from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Issue
from app.repository.issue_repository import IssueRepository
from app.schemas.issue import IssueCreate, IssueUpdate

class IssueService:
    """Business logic layer for Issue operations."""

    def __init__(self, db: Session):
        # Service creates and owns the repository instance
        self.repo = IssueRepository(db)

    def get_all_issues(self) -> list[Issue]:
        """Return all issues."""
        return self.repo.get_all()

    def get_issue_by_id(self, issue_id: int) -> Issue:
        """Return a single issue, or raise 404 if not found."""
        issue = self.repo.get_by_id(issue_id)
        if issue is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with id {issue_id} not found",
            )
        return issue

    def create_issue(self, data: IssueCreate) -> Issue:
        """Create and return a new issue."""
        return self.repo.create(data)

    def update_issue(self, issue_id: int, data: IssueUpdate) -> Issue:
        """Update an existing issue. Raises 404 if issue doesn't exist."""
        issue = self.get_issue_by_id(issue_id)
        return self.repo.update(issue, data)

    def delete_issue(self, issue_id: int) -> None:
        """Delete an issue. Raises 404 if issue doesn't exist."""
        issue = self.get_issue_by_id(issue_id)
        self.repo.delete(issue)
