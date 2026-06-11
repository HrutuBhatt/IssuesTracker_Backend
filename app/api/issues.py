from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.issue import IssueCreate, IssueResponse, IssueUpdate
from app.services.issue_service import IssueService
from app.auth.dependencies import get_current_user
from app.models.models import User

router = APIRouter(prefix="/api/issues", tags=["Issues"])


@router.get("/", response_model=list[IssueResponse])
def get_all_issues(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all issues."""
    service = IssueService(db)
    return service.get_all_issues()


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a single issue by ID. Returns 404 if not found."""
    service = IssueService(db)
    return service.get_issue_by_id(issue_id)


@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    data: IssueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new issue. Title is required."""
    service = IssueService(db)
    return service.create_issue(data)


@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    data: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing issue. All fields optional. Returns 404 if not found."""
    service = IssueService(db)
    return service.update_issue(issue_id, data)


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an issue by ID. Returns 404 if not found."""
    service = IssueService(db)
    service.delete_issue(issue_id)

