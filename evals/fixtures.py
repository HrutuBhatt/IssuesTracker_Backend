"""Seed and teardown a fixed test project for eval runs."""

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

import bcrypt as _bcrypt

from sqlalchemy.orm import Session

from app.models.models import (
    User, Project, ProjectMember, ProjectRole,
    Issue, IssueStatus, IssuePriority, IssueType,
)

_HASH = _bcrypt.hashpw(b"evalpass123", _bcrypt.gensalt()).decode("utf-8")


@dataclass
class FixtureData:
    project_id: int
    admin_id: int
    dev1_id: int        # has DB-related closed issue history
    dev2_id: int        # has auth-related closed issue history
    client_id: int
    open_issue_ids: list[int]           # open assigned issues
    unassigned_recent_ids: list[int]    # unassigned bugs created ~1h ago (bulk triage)
    closed_issue_ids: list[int]         # closed issues (developer history)


_EVAL_EMAILS = [
    "eval_admin@test.com",
    "eval_dev1@test.com",
    "eval_dev2@test.com",
    "eval_client@test.com",
]


def _cleanup_stale(db: Session) -> None:
    """Remove any leftover eval data from a previously crashed run."""
    stale_users = db.query(User).filter(User.email.in_(_EVAL_EMAILS)).all()
    if not stale_users:
        return
    stale_ids = [u.id for u in stale_users]
    stale_projects = db.query(Project).filter(Project.created_by.in_(stale_ids)).all()
    for project in stale_projects:
        from app.models.models import IssueHistory
        db.query(IssueHistory).filter(
            IssueHistory.issue_id.in_(
                db.query(Issue.id).filter(Issue.project_id == project.id)
            )
        ).delete(synchronize_session=False)
        db.query(Issue).filter(Issue.project_id == project.id).delete()
        db.query(ProjectMember).filter(ProjectMember.project_id == project.id).delete()
    db.query(Project).filter(Project.created_by.in_(stale_ids)).delete()
    db.query(User).filter(User.email.in_(_EVAL_EMAILS)).delete()
    db.commit()
    print("[Fixtures] Cleaned up stale eval data from a previous run.")


def seed(db: Session) -> FixtureData:
    _cleanup_stale(db)

    # ── Users ──────────────────────────────────────────────────────────────
    admin  = User(email="eval_admin@test.com",  hashed_password=_HASH)
    dev1   = User(email="eval_dev1@test.com",   hashed_password=_HASH)
    dev2   = User(email="eval_dev2@test.com",   hashed_password=_HASH)
    client = User(email="eval_client@test.com", hashed_password=_HASH)
    db.add_all([admin, dev1, dev2, client])
    db.flush()

    # ── Project ────────────────────────────────────────────────────────────
    project = Project(name="Eval Test Project", created_by=admin.id)
    db.add(project)
    db.flush()

    # ── Members ────────────────────────────────────────────────────────────
    db.add_all([
        ProjectMember(project_id=project.id, user_id=admin.id,   role=ProjectRole.ADMIN),
        ProjectMember(project_id=project.id, user_id=dev1.id,    role=ProjectRole.DEVELOPER),
        ProjectMember(project_id=project.id, user_id=dev2.id,    role=ProjectRole.DEVELOPER),
        ProjectMember(project_id=project.id, user_id=client.id,  role=ProjectRole.CLIENT),
    ])

    now    = datetime.now(timezone.utc)
    recent = now - timedelta(hours=1)

    # ── Closed issues — developer history ─────────────────────────────────
    # dev1 has DB experience
    c1 = Issue(project_id=project.id, created_by=admin.id, assigned_to=dev1.id,
               title="Fix database connection timeout", status=IssueStatus.CLOSED,
               priority=IssuePriority.HIGH, issue_type=IssueType.BUG)
    c2 = Issue(project_id=project.id, created_by=admin.id, assigned_to=dev1.id,
               title="Resolve DB pool exhaustion under load", status=IssueStatus.CLOSED,
               priority=IssuePriority.HIGH, issue_type=IssueType.BUG)
    # dev2 has auth experience
    c3 = Issue(project_id=project.id, created_by=admin.id, assigned_to=dev2.id,
               title="Fix authentication token expiry bug", status=IssueStatus.CLOSED,
               priority=IssuePriority.MEDIUM, issue_type=IssueType.BUG)
    c4 = Issue(project_id=project.id, created_by=admin.id, assigned_to=dev2.id,
               title="Resolve session invalidation on logout", status=IssueStatus.CLOSED,
               priority=IssuePriority.MEDIUM, issue_type=IssueType.BUG)
    db.add_all([c1, c2, c3, c4])

    # ── Open assigned issues ───────────────────────────────────────────────
    o1 = Issue(project_id=project.id, created_by=admin.id, assigned_to=dev1.id,
               title="Dashboard charts not loading", status=IssueStatus.OPEN,
               priority=IssuePriority.MEDIUM, issue_type=IssueType.BUG)
    o2 = Issue(project_id=project.id, created_by=admin.id, assigned_to=dev2.id,
               title="User profile page throws 500", status=IssueStatus.OPEN,
               priority=IssuePriority.HIGH, issue_type=IssueType.BUG)
    db.add_all([o1, o2])

    # ── Unassigned recent bugs — for bulk triage ───────────────────────────
    u1 = Issue(project_id=project.id, created_by=admin.id, assigned_to=None,
               title="Cannot connect to database", status=IssueStatus.OPEN,
               priority=IssuePriority.HIGH, issue_type=IssueType.BUG,
               created_at=recent)
    u2 = Issue(project_id=project.id, created_by=admin.id, assigned_to=None,
               title="DB query times out on search page", status=IssueStatus.OPEN,
               priority=IssuePriority.HIGH, issue_type=IssueType.BUG,
               created_at=recent)
    u3 = Issue(project_id=project.id, created_by=admin.id, assigned_to=None,
               title="Login fails with invalid token error", status=IssueStatus.OPEN,
               priority=IssuePriority.HIGH, issue_type=IssueType.BUG,
               created_at=recent)
    u4 = Issue(project_id=project.id, created_by=admin.id, assigned_to=None,
               title="Auth session expires without warning", status=IssueStatus.OPEN,
               priority=IssuePriority.HIGH, issue_type=IssueType.BUG,
               created_at=recent)
    db.add_all([u1, u2, u3, u4])

    db.commit()
    for obj in [admin, dev1, dev2, client, project, c1, c2, c3, c4, o1, o2, u1, u2, u3, u4]:
        db.refresh(obj)

    return FixtureData(
        project_id=project.id,
        admin_id=admin.id,
        dev1_id=dev1.id,
        dev2_id=dev2.id,
        client_id=client.id,
        open_issue_ids=[o1.id, o2.id],
        unassigned_recent_ids=[u1.id, u2.id, u3.id, u4.id],
        closed_issue_ids=[c1.id, c2.id, c3.id, c4.id],
    )


def teardown(db: Session, fx: FixtureData) -> None:
    from app.models.models import IssueHistory
    db.query(IssueHistory).filter(
        IssueHistory.issue_id.in_(
            db.query(Issue.id).filter(Issue.project_id == fx.project_id)
        )
    ).delete(synchronize_session=False)
    db.query(Issue).filter(Issue.project_id == fx.project_id).delete()
    db.query(ProjectMember).filter(ProjectMember.project_id == fx.project_id).delete()
    db.query(Project).filter(Project.id == fx.project_id).delete()
    for uid in [fx.admin_id, fx.dev1_id, fx.dev2_id, fx.client_id]:
        db.query(User).filter(User.id == uid).delete()
    db.commit()
