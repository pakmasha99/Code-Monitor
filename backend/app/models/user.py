"""
User model - represents lab members
"""
from datetime import date
from typing import List, Optional
from sqlalchemy import String, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from backend.app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """User roles in the system"""
    STUDENT = "student"
    ADVISOR = "advisor"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    """
    User model representing lab members.

    Attributes:
        id: Primary key
        name: Full name of the user
        email: Email address (unique)
        github_username: GitHub username for repo access
        repo_url: Git repository URL
        joined_date: Date when user joined the lab
        role: User role (student/advisor/admin)
        is_active: Whether the user account is active
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    github_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    repo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    joined_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.STUDENT,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    weekly_submissions: Mapped[List["WeeklySubmission"]] = relationship(
        "WeeklySubmission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    git_metrics: Mapped[List["GitMetrics"]] = relationship(
        "GitMetrics",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    rankings: Mapped[List["Ranking"]] = relationship(
        "Ranking",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    code_analyses: Mapped[List["CodeAnalysis"]] = relationship(
        "CodeAnalysis",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
