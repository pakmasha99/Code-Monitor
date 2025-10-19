"""
API endpoints for rankings
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.ranking import (
    RankingResponse,
    RankingHistory,
    RankingUpdateResponse
)
from app.services.ranking_service import RankingService

router = APIRouter(prefix="/api/rankings", tags=["Rankings"])


@router.get("/current", response_model=List[RankingResponse])
def get_current_week_rankings(db: Session = Depends(get_db)):
    """
    Get rankings for the current week.

    Returns rankings ordered by position (best to worst).
    """
    service = RankingService()
    week_start = service.get_current_week_start()

    rankings = service.get_weekly_rankings(week_start, db)

    return rankings


@router.get("/week/{week_start_date}", response_model=List[RankingResponse])
def get_specific_week_rankings(
    week_start_date: date = Path(..., description="Monday of the week (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get rankings for a specific week.

    - **week_start_date**: Monday of the week (YYYY-MM-DD format)
    """
    service = RankingService()
    rankings = service.get_weekly_rankings(week_start_date, db)

    return rankings


@router.get("/top/{n}", response_model=List[RankingResponse])
def get_top_performers(
    n: int = Path(..., ge=1, le=100, description="Number of top performers"),
    week_start_date: Optional[date] = Query(None, description="Week start date, defaults to current week"),
    db: Session = Depends(get_db)
):
    """
    Get top N performers for a specific week.

    - **n**: Number of top performers to return (1-100)
    - **week_start_date**: Optional week start date, defaults to current week
    """
    service = RankingService()

    if week_start_date is None:
        week_start_date = service.get_current_week_start()

    top_performers = service.get_top_performers(week_start_date, limit=n, db=db)

    return top_performers


@router.post("/update/{week_start_date}", response_model=RankingUpdateResponse)
def trigger_ranking_update(
    week_start_date: date = Path(..., description="Monday of the week (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger ranking calculation for a specific week.

    This will:
    1. Calculate scores for all users based on git metrics and submissions
    2. Update or create rankings for the week
    3. Assign rank positions

    - **week_start_date**: Monday of the week to update
    """
    service = RankingService()
    result = service.update_weekly_rankings(week_start_date, db)

    return RankingUpdateResponse(
        status="success",
        total_users=result["total_users"],
        updated=result["updated"],
        week_start_date=result["week_start_date"]
    )
