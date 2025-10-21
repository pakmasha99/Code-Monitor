"""
API endpoints for weekly submissions
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.weekly_submission import WeeklySubmission
from app.schemas.weekly_submission import (
    WeeklySubmissionCreate,
    WeeklySubmissionUpdate,
    WeeklySubmissionResponse,
    WeeklySubmissionWithUser
)
from app.services.ranking_service import RankingService
from app.api.git_stats import validate_github_url

router = APIRouter(prefix="/api", tags=["Weekly Submissions"])


def get_week_start_date(date_obj: datetime) -> date:
    """Get Monday of the week for a given date"""
    return (date_obj - timedelta(days=date_obj.weekday())).date()


@router.post("/users/{user_id}/submissions", response_model=WeeklySubmissionResponse, status_code=201)
def create_weekly_submission(
    user_id: int,
    submission_data: WeeklySubmissionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a weekly submission for a user.

    - **user_id**: ID of the user submitting
    - **week_start_date**: Monday of the week (auto-calculated if not provided)
    - **code_lines_added**: Lines of code added
    - **documents_created**: Number of documents created
    - **notes**: Optional notes about the week
    - **custom_repo_url**: Optional custom repository URL to use instead of user's default repo
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if submission already exists for this week
    existing = db.query(WeeklySubmission).filter(
        WeeklySubmission.user_id == user_id,
        WeeklySubmission.week_start_date == submission_data.week_start_date
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Submission already exists for week starting {submission_data.week_start_date}"
        )

    # Determine which repository URLs to use (supports multiple repos)
    effective_repo_urls = []

    # Priority: custom_repo_urls > custom_repo_url > user.repo_url
    if submission_data.custom_repo_urls:
        effective_repo_urls = submission_data.custom_repo_urls
    elif submission_data.custom_repo_url:
        # Backward compatibility: single custom_repo_url
        effective_repo_urls = [submission_data.custom_repo_url]
    elif user.repo_url:
        effective_repo_urls = [user.repo_url]
    else:
        raise HTTPException(
            status_code=400,
            detail="No repository URL available. Please provide custom_repo_urls or update user profile."
        )

    # Security: Validate all GitHub URLs
    for repo_url in effective_repo_urls:
        if not validate_github_url(repo_url):
            raise HTTPException(
                status_code=400,
                detail=f"Only GitHub URLs are allowed. Invalid URL: {repo_url}"
            )

    # Store repository URLs as comma-separated string
    repository_url_str = ",".join(effective_repo_urls)

    # Create submission with repository_url
    submission_dict = submission_data.model_dump(exclude={'custom_repo_url', 'custom_repo_urls'})
    submission = WeeklySubmission(
        user_id=user_id,
        repository_url=repository_url_str,
        **submission_dict
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Automatically update rankings for this week
    ranking_service = RankingService()
    ranking_service.update_weekly_rankings(submission.week_start_date, db)

    return submission


@router.get("/users/{user_id}/submissions", response_model=List[WeeklySubmissionResponse])
def get_user_submissions(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all weekly submissions for a specific user.

    Returns submissions ordered by week (most recent first).
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get submissions
    submissions = db.query(WeeklySubmission).filter(
        WeeklySubmission.user_id == user_id
    ).order_by(
        WeeklySubmission.week_start_date.desc()
    ).offset(skip).limit(limit).all()

    return submissions


@router.get("/submissions", response_model=List[WeeklySubmissionWithUser])
def get_all_submissions(
    week_start_date: Optional[date] = Query(None, description="Filter by specific week"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all weekly submissions across all users.

    Optional filtering by week. Returns submissions with user information.
    """
    query = db.query(WeeklySubmission).join(User)

    if week_start_date:
        query = query.filter(WeeklySubmission.week_start_date == week_start_date)

    submissions = query.order_by(
        WeeklySubmission.week_start_date.desc(),
        User.name
    ).offset(skip).limit(limit).all()

    # Format response with user info
    result = []
    for submission in submissions:
        result.append({
            "id": submission.id,
            "user_id": submission.user_id,
            "week_start_date": submission.week_start_date,
            "code_lines_added": submission.code_lines_added,
            "documents_created": submission.documents_created,
            "notes": submission.notes,
            "user_name": submission.user.name,
            "user_email": submission.user.email
        })

    return result


@router.get("/users/{user_id}/submissions/{submission_id}", response_model=WeeklySubmissionResponse)
def get_submission(
    user_id: int,
    submission_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific weekly submission by ID."""
    submission = db.query(WeeklySubmission).filter(
        WeeklySubmission.id == submission_id,
        WeeklySubmission.user_id == user_id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return submission


@router.patch("/users/{user_id}/submissions/{submission_id}", response_model=WeeklySubmissionResponse)
def update_submission(
    user_id: int,
    submission_id: int,
    update_data: WeeklySubmissionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a weekly submission.

    Only the fields provided will be updated.
    """
    submission = db.query(WeeklySubmission).filter(
        WeeklySubmission.id == submission_id,
        WeeklySubmission.user_id == user_id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(submission, field, value)

    db.commit()
    db.refresh(submission)

    # Automatically update rankings for this week
    ranking_service = RankingService()
    ranking_service.update_weekly_rankings(submission.week_start_date, db)

    return submission


@router.delete("/users/{user_id}/submissions/{submission_id}", status_code=204)
def delete_submission(
    user_id: int,
    submission_id: int,
    db: Session = Depends(get_db)
):
    """Delete a weekly submission."""
    submission = db.query(WeeklySubmission).filter(
        WeeklySubmission.id == submission_id,
        WeeklySubmission.user_id == user_id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    db.delete(submission)
    db.commit()

    return None


@router.get("/submissions/current-week", response_model=List[WeeklySubmissionWithUser])
def get_current_week_submissions(db: Session = Depends(get_db)):
    """
    Get all submissions for the current week.

    Useful for dashboard display of this week's progress.
    """
    # Get current week start date (Monday)
    now = datetime.utcnow()
    week_start = get_week_start_date(now)

    submissions = db.query(WeeklySubmission).join(User).filter(
        WeeklySubmission.week_start_date == week_start
    ).order_by(User.name).all()

    # Format response with user info
    result = []
    for submission in submissions:
        result.append({
            "id": submission.id,
            "user_id": submission.user_id,
            "week_start_date": submission.week_start_date,
            "code_lines_added": submission.code_lines_added,
            "documents_created": submission.documents_created,
            "notes": submission.notes,
            "user_name": submission.user.name,
            "user_email": submission.user.email
        })

    return result
