from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.schemas.issue import IssueCreate, IssueUpdate


class IssueRepository:
    """Handles all database operations for the Issue model."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Issue]:
        """Fetch all issues from the database."""
        return self.db.query(Issue).all()

    def get_by_id(self, issue_id: int) -> Issue | None:
        """Fetch a single issue by its ID. Returns None if not found."""
        return self.db.query(Issue).filter(Issue.id == issue_id).first()

    def create(self, data: IssueCreate) -> Issue:
        """Create and persist a new issue."""
        issue = Issue(**data.model_dump())
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def update(self, issue: Issue, data: IssueUpdate) -> Issue:
        """Update only the fields the client provided."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(issue, field, value)
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def delete(self, issue: Issue) -> None:
        """Delete an issue from the database."""
        self.db.delete(issue)
        self.db.commit()
