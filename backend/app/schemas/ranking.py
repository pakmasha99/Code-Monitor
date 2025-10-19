"""
Pydantic schemas for ranking API
"""
from datetime import date
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RankingResponse(BaseModel):
    """Schema for ranking response"""
    rank_position: int
    user_id: int
    user_name: str
    user_email: str
    total_score: float
    category_scores: Dict[str, float]
    week_start_date: str

    class Config:
        from_attributes = True


class RankingHistory(BaseModel):
    """Schema for user ranking history"""
    week_start_date: str
    rank_position: int
    total_score: float
    category_scores: Dict[str, float]

    class Config:
        from_attributes = True


class RankingUpdateResponse(BaseModel):
    """Schema for ranking update response"""
    status: str
    total_users: int
    updated: int
    week_start_date: str
