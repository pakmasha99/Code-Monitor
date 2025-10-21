"""
Git statistics API endpoints
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from git import GitCommandError

from app.core.database import get_db
from app.models.user import User
from app.schemas.git_stats import GitStatsResponse
from app.services.git_service import GitSyncService

router = APIRouter(prefix="/api", tags=["Git Stats"])


def validate_github_url(url: str) -> bool:
    """Validate that URL is a GitHub repository URL"""
    return url.startswith("https://github.com/") or url.startswith("git@github.com:")


@router.get("/users/{user_id}/git-stats", response_model=GitStatsResponse)
def get_git_stats(
    user_id: int,
    since: datetime = Query(..., description="Analyze commits since this date"),
    repo_url: Optional[str] = Query(None, description="Override user's stored repo_url"),
    db: Session = Depends(get_db)
) -> GitStatsResponse:
    """
    Fetch git statistics for a user's repository.

    This endpoint analyzes the user's git repository and returns metrics like
    commits count, lines added/deleted, and language breakdown.

    **Parameters:**
    - user_id: User ID
    - since: Start date for commit analysis (ISO 8601 format)
    - repo_url: (Optional) Override the user's stored repository URL

    **Returns:**
    - Git statistics including commits, lines changed, and language breakdown

    **Errors:**
    - 404: User not found
    - 400: No repository URL available or invalid URL
    - 500: Git operation failed (clone, pull, or analysis error)
    """
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Determine which repo_url to use
    effective_repo_url = repo_url if repo_url else user.repo_url

    if not effective_repo_url:
        raise HTTPException(
            status_code=400,
            detail="No repository URL available. Please provide repo_url parameter or update user profile."
        )

    # Security: Only allow GitHub URLs
    if not validate_github_url(effective_repo_url):
        raise HTTPException(
            status_code=400,
            detail="Only GitHub URLs are allowed for security reasons."
        )

    # Initialize GitSyncService
    git_service = GitSyncService()

    try:
        # Clone or pull repository
        repo = git_service.clone_or_pull(effective_repo_url, user_id)

        # Get commits since specified date
        commits = git_service.get_commits_since(repo, since)

        # Analyze commits
        stats = git_service.analyze_commits(repo, commits)

        # Return response
        return GitStatsResponse(
            commits_count=stats['commits_count'],
            files_changed=stats['files_changed'],
            lines_added=stats['lines_added'],
            lines_deleted=stats['lines_deleted'],
            languages_breakdown=stats['languages_breakdown'],
            analyzed_since=since,
            repo_url=effective_repo_url
        )

    except GitCommandError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Git operation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze repository: {str(e)}"
        )
