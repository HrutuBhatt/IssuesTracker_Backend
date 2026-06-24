from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload

from app.models.models import Issue, ProjectMember, ProjectRole
from app.schemas.issue import IssueCreate, IssueUpdate, IssueResponse
from app.services.issue_service import IssueService


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_issues",
            "description": (
                "Retrieve all issues for the current project. "
                "Always call this before update_issue to confirm real issue IDs. "
                "Returns id, title, status, assigned_to (user_id), assigned_to_email, and created_at for each issue."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "description": "Optional. Limit results to this status only.",
                        "enum": ["open", "in_progress", "closed"],
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_issues",
            "description": (
                "Return aggregate statistics about the project's issues. "
                "Use for count queries, status breakdowns, or age reports — not for fetching issue IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "description": "How to group the summary. Defaults to 'status'.",
                        "enum": ["status", "assigned_to", "age"],
                    },
                    "status_filter": {
                        "type": "string",
                        "description": "Optional. Restrict the summary to issues with this status.",
                        "enum": ["open", "in_progress", "closed"],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_issue",
            "description": (
                "Create a single new issue in the current project. "
                "Only use when the user explicitly requests issue creation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Issue title. Required. Must not be blank. Max 200 characters.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional detailed description.",
                    },
                    "assigned_to": {
                        "type": "integer",
                        "description": "Optional. User ID of the assignee from the project member list.",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_issue",
            "description": (
                "Update fields on a single issue by its ID. "
                "For bulk updates, call this once per issue. "
                "Always call list_issues first to obtain real issue IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "integer",
                        "description": "ID of the issue to update.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional. New title for the issue.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional. New description for the issue.",
                    },
                    "status": {
                        "type": "string",
                        "description": "Optional. New status.",
                        "enum": ["open", "in_progress", "closed"],
                    },
                    "assigned_to": {
                        "type": "integer",
                        "description": "Optional. User ID to assign the issue to.",
                    },
                    "unassign": {
                        "type": "boolean",
                        "description": "Optional. Set to true to remove the current assignee. Takes precedence over assigned_to.",
                    },
                },
                "required": ["issue_id"],
            },
        },
    },
]


class ToolExecutor:
    """Executes tool calls on behalf of the agent. Stateful — holds a db session."""

    def __init__(self, db: Session):
        self.db = db
        self._issue_service = IssueService(db)

    def execute(
        self,
        name: str,
        args: dict,
        project_id: int,
        actor_id: int,
        actor_role: ProjectRole,
    ):
        if name == "list_issues":
            return self._list_issues(args, project_id)
        if name == "summarize_issues":
            return self._summarize_issues(args, project_id)
        if name == "create_issue":
            return self._create_issue(args, project_id, actor_id, actor_role)
        if name == "update_issue":
            return self._update_issue(args, project_id, actor_id, actor_role)
        raise ValueError(f"Unknown tool: {name}")

    # ------------------------------------------------------------------
    # Public helpers used by AssistantService for system prompt building
    # ------------------------------------------------------------------

    def get_all_issues(self, project_id: int) -> list[Issue]:
        return self._issue_service.get_all_issues(project_id)

    def get_members(self, project_id: int) -> list[ProjectMember]:
        return (
            self.db.query(ProjectMember)
            .options(joinedload(ProjectMember.user))
            .filter(ProjectMember.project_id == project_id)
            .all()
        )

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _list_issues(self, args: dict, project_id: int) -> list:
        issues = self._get_filtered_issues(project_id, args.get("status_filter"))
        member_map = self._get_member_map(project_id)
        result = []
        for issue in issues:
            data = self._serialize_issue(issue)
            data["assigned_to_email"] = member_map.get(issue.assigned_to, "unassigned")
            result.append(data)
        return result

    def _summarize_issues(self, args: dict, project_id: int) -> dict:
        issues = self._get_filtered_issues(project_id, args.get("status_filter"))
        group_by = args.get("group_by", "status")
        now = datetime.now(timezone.utc)

        if group_by == "status":
            counts: dict = {"open": 0, "in_progress": 0, "closed": 0}
            for issue in issues:
                counts[issue.status.value] = counts.get(issue.status.value, 0) + 1
            return {"total": len(issues), "by_stacntus": counts}

        if group_by == "assigned_to":
            counts = {}
            for issue in issues:
                key = str(issue.assigned_to) if issue.assigned_to else "unassigned"
                counts[key] = counts.get(key, 0) + 1
            return {"total": len(issues), "by_assignee": counts}

        if group_by == "age":
            buckets = {"last_7_days": 0, "last_30_days": 0, "older": 0}
            for issue in issues:
                created = issue.created_at
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                age_days = (now - created).days
                if age_days <= 7:
                    buckets["last_7_days"] += 1
                elif age_days <= 30:
                    buckets["last_30_days"] += 1
                else:
                    buckets["older"] += 1
            return {"total": len(issues), "by_age": buckets}

        return {"total": len(issues)}

    def _create_issue(
        self,
        args: dict,
        project_id: int,
        actor_id: int,
        actor_role: ProjectRole,
    ) -> dict:
        if actor_role not in (ProjectRole.ADMIN, ProjectRole.DEVELOPER):
            raise PermissionError("Your role does not allow creating issues.")

        data = IssueCreate(
            title=args["title"],
            description=args.get("description"),
            assigned_to=args.get("assigned_to"),
        )
        issue = self._issue_service.create_issue(project_id, actor_id, data)
        return self._serialize_issue(issue)

    def _update_issue(
        self,
        args: dict,
        project_id: int,
        actor_id: int,
        actor_role: ProjectRole,
    ) -> dict:
        if actor_role not in (ProjectRole.ADMIN, ProjectRole.DEVELOPER):
            raise PermissionError("Your role does not allow updating issues.")

        issue_id = int(args["issue_id"])
        existing = self._issue_service.get_issue_by_id(issue_id)

        if existing.project_id != project_id:
            raise PermissionError("Issue does not belong to this project.")

        update_kwargs: dict = {"title": args.get("title", existing.title)}

        if "description" in args:
            update_kwargs["description"] = args["description"]
        if "status" in args:
            update_kwargs["status"] = args["status"]
        if args.get("unassign"):
            update_kwargs["assigned_to"] = None
        elif "assigned_to" in args:
            update_kwargs["assigned_to"] = int(args["assigned_to"])

        data = IssueUpdate(**update_kwargs)
        updated = self._issue_service.update_issue(issue_id, data, actor_id)
        return self._serialize_issue(updated)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_filtered_issues(self, project_id: int, status_filter: str | None) -> list[Issue]:
        issues = self._issue_service.get_all_issues(project_id)
        if status_filter:
            issues = [i for i in issues if i.status.value == status_filter]
        return issues

    def _get_member_map(self, project_id: int) -> dict[int, str]:
        members = self.get_members(project_id)
        return {m.user_id: m.user.email for m in members if m.user}

    def _serialize_issue(self, issue: Issue) -> dict:
        return IssueResponse.model_validate(issue).model_dump(mode="json")
