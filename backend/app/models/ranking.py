"""
Ranking model - weekly rankings for users
"""
from datetime import date
from typing import Optional, Dict, Any
from sqlalchemy import Float, Integer, Date, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class Ranking(Base):
    """
    Ranking model for weekly performance scores.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        week_start_date: Monday of the week
        total_score: Calculated total score (0-100)
        rank_position: Position in rankings (1 = first)
        category_scores: JSON with breakdown {"code": 80, "docs": 60, "quality": 75, "sharing": 40}
    """
    __tablename__ = "rankings"
    __table_args__ = (
        UniqueConstraint('user_id', 'week_start_date', name='uq_ranking_user_week'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rank_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    category_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="rankings")

    def __repr__(self) -> str:
        return f"<Ranking(id={self.id}, user_id={self.user_id}, week={self.week_start_date}, rank={self.rank_position})>"
