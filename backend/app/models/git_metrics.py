"""
GitMetrics model - automated git analysis results
"""
from datetime import date, datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class GitMetrics(Base):
    """
    Git metrics model for automated repository analysis.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        repo_url: Repository URL analyzed
        week_start_date: Monday of the week
        commits_count: Number of commits this week
        files_changed: Number of files changed
        lines_added: Lines of code added
        lines_deleted: Lines of code deleted
        languages_breakdown: JSON with language distribution {"Python": 1200, "JS": 340}
        last_sync_timestamp: When the last sync occurred
    """
    __tablename__ = "git_metrics"
    __table_args__ = (
        UniqueConstraint('user_id', 'week_start_date', name='uq_git_user_week'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    repo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    commits_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_changed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lines_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lines_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    languages_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    last_sync_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="git_metrics")

    def __repr__(self) -> str:
        return f"<GitMetrics(id={self.id}, user_id={self.user_id}, week={self.week_start_date}, commits={self.commits_count})>"
