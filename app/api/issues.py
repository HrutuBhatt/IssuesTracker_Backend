from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.issue import IssueCreate, IssueResponse, IssueUpdate, IssueHistoryResponse
from app.services.issue_service import IssueService
from app.auth.dependencies import get_current_user, require_project_membership, require_issue_permission
from app.models.models import User, ProjectRole, Issue, ProjectMember

router = APIRouter(tags=["Issues"])


@router.get("/api/projects/{project_id}/issues", response_model=list[IssueResponse])
def get_project_issues(
    project_id: int,
    current_user: User = Depends(get_current_user),
    project_member: ProjectMember = Depends(require_project_membership([ProjectRole.ADMIN, ProjectRole.DEVELOPER, ProjectRole.CLIENT])),
    db: Session = Depends(get_db)
):
    """Retrieve all issues for a specific project."""
    service = IssueService(db)
    return service.get_all_issues(project_id)


@router.post("/api/projects/{project_id}/issues", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    project_id: int,
    data: IssueCreate,
    current_user: User = Depends(get_current_user),
    project_member: ProjectMember = Depends(require_project_membership([ProjectRole.ADMIN, ProjectRole.DEVELOPER])),
    db: Session = Depends(get_db)
):
    """Create a new issue inside a project."""
    service = IssueService(db)
    return service.create_issue(project_id, current_user.id, data)


@router.get("/api/issues/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    issue: Issue = Depends(require_issue_permission([ProjectRole.ADMIN, ProjectRole.DEVELOPER, ProjectRole.CLIENT])),
    db: Session = Depends(get_db)
):
    """Retrieve a single issue by ID. Requires project membership."""
    # require_issue_permission already checked permissions and fetched the issue
    return issue


@router.put("/api/issues/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    data: IssueUpdate,
    current_user: User = Depends(get_current_user),
    issue: Issue = Depends(require_issue_permission([ProjectRole.ADMIN, ProjectRole.DEVELOPER])),
    db: Session = Depends(get_db)
):
    """Update an existing issue. Audits changes."""
    service = IssueService(db)
    return service.update_issue(issue_id, data, current_user.id)


@router.delete("/api/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    issue: Issue = Depends(require_issue_permission([ProjectRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Soft-delete an issue by ID. Requires Project ADMIN role."""
    service = IssueService(db)
    service.delete_issue(issue_id)


@router.get("/api/issues/{issue_id}/history", response_model=list[IssueHistoryResponse])
def get_issue_history(
    issue_id: int,
    issue: Issue = Depends(require_issue_permission([ProjectRole.ADMIN, ProjectRole.DEVELOPER, ProjectRole.CLIENT])),
    db: Session = Depends(get_db)
):
    """Retrieve the change history log for an issue."""
    service = IssueService(db)
    return service.get_issue_history(issue_id)
