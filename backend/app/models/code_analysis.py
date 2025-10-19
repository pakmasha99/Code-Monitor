"""
CodeAnalysis model - LLM-based code analysis results
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class CodeAnalysis(Base):
    """
    Code analysis model for LLM-generated insights (Phase 3).

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        file_path: Path to the analyzed file
        commit_hash: Git commit SHA
        function_name: Name of function/method analyzed
        class_name: Name of class if applicable
        analysis_summary: LLM-generated summary
        complexity_score: Code complexity score (1-10)
        quality_metrics: JSON with detailed metrics
        analyzed_at: When analysis was performed
    """
    __tablename__ = "code_analysis"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    commit_hash: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    function_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    class_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    complexity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="code_analyses")

    def __repr__(self) -> str:
        return f"<CodeAnalysis(id={self.id}, user_id={self.user_id}, file='{self.file_path}')>"
