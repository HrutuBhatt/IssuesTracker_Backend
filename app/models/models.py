import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text

from app.db.database import Base


class IssueStatus(str, enum.Enum):
    """Allowed values for the status field."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    CLOSED = "Closed"


class Issue(Base):
    __tablename__ = "issues"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(Enum(IssueStatus), default=IssueStatus.OPEN, nullable=False)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = Column(DateTime, nullable=True,
                         onupdate=lambda: datetime.now(timezone.utc))
    deleted_at  = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    email       = Column(String(200), nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, nullable=False)
    refresh_token = Column(String(200), nullable=False)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    