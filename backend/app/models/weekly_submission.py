"""
WeeklySubmission model - user's weekly manual submissions
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WeeklySubmission(Base):
    """
    Weekly submission model for manual user inputs.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        week_start_date: Monday of the week (ISO week start)
        code_lines_added: Self-reported lines of code added
        code_lines_modified: Self-reported lines of code modified
        documents_created: Number of documents created this week
        documents_modified: Number of documents modified this week
        notes: Free-text weekly notes/summary
        repository_url: The actual repository URL used for this submission
        submission_timestamp: When the submission was made
    """
    __tablename__ = "weekly_submissions"
    __table_args__ = (
        UniqueConstraint('user_id', 'week_start_date', name='uq_user_week'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    code_lines_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    code_lines_modified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_modified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    repository_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    submission_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="weekly_submissions")

    def __repr__(self) -> str:
        return f"<WeeklySubmission(id={self.id}, user_id={self.user_id}, week={self.week_start_date})>"
