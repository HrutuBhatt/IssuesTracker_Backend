import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    email       = Column(String(200), nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    creator = relationship("User", foreign_keys=[created_by])


class ProjectRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    CLIENT = "client"


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(ProjectRole), default=ProjectRole.CLIENT, nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
    )

    project = relationship("Project", backref="members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""


class IssueStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True)

    project = relationship("Project", backref="issues")
    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])


class IssueHistory(Base):
    __tablename__ = "issue_history"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    field_changed = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    issue = relationship("Issue", backref="history")
    user = relationship("User", foreign_keys=[changed_by])