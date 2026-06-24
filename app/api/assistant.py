from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import User, ProjectMember, ProjectRole
from app.auth.dependencies import get_current_user, require_project_membership
from app.services.assistant_client import AssistantClient, get_assistant_client
from app.services.assistant_service import AssistantService
from app.schemas import AssistantRequest, AssistantResponse

router = APIRouter(tags=["Assistant"])


@router.post("/api/projects/{project_id}/assistant", response_model=AssistantResponse)
def run_assistant(
    project_id: int,
    body: AssistantRequest,
    current_user: User = Depends(get_current_user),
    project_member: ProjectMember = Depends(
        require_project_membership([ProjectRole.ADMIN, ProjectRole.DEVELOPER, ProjectRole.CLIENT])
    ),
    db: Session = Depends(get_db),
    assistant_client: AssistantClient = Depends(get_assistant_client),
):
    try:
        service = AssistantService(assistant_client, db)
        reply, issues_modified = service.run_agent(
            prompt=body.prompt,
            project_id=project_id,
            actor_id=current_user.id,
            actor_role=project_member.role,
            history=[m.model_dump() for m in body.history],
        )
        return AssistantResponse(reply=reply, issues_modified=issues_modified)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI assistant is temporarily unavailable. Please try again.",
        )
