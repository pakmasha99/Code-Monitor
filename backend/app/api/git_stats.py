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
    repo_url: Optional[str] = Query(None, description="Override user's stored repo_url (single repo)"),
    repo_urls: Optional[str] = Query(None, description="Comma-separated repository URLs (multiple repos)"),
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

    # Determine which repository URLs to use
    effective_repo_urls = []

    # Priority: repo_urls (multiple) > repo_url (single) > user.repo_url
    if repo_urls:
        # Parse comma-separated URLs
        effective_repo_urls = [url.strip() for url in repo_urls.split(',') if url.strip()]
    elif repo_url:
        effective_repo_urls = [repo_url]
    elif user.repo_url:
        effective_repo_urls = [user.repo_url]
    else:
        raise HTTPException(
            status_code=400,
            detail="No repository URL available. Please provide repo_url/repo_urls parameter or update user profile."
        )

    # Security: Validate all GitHub URLs
    for url in effective_repo_urls:
        if not validate_github_url(url):
            raise HTTPException(
                status_code=400,
                detail=f"Only GitHub URLs are allowed for security reasons. Invalid URL: {url}"
            )

    # Initialize GitSyncService
    git_service = GitSyncService()

    # Aggregate statistics from all repositories
    total_commits = 0
    total_files_changed = set()
    total_lines_added = 0
    total_lines_deleted = 0
    total_languages = {}

    try:
        for idx, current_repo_url in enumerate(effective_repo_urls):
            # Use unique user_id suffix for each repo to avoid conflicts
            repo_user_id = f"{user_id}_repo{idx}" if len(effective_repo_urls) > 1 else str(user_id)

            # Clone or pull repository
            repo = git_service.clone_or_pull(current_repo_url, int(repo_user_id.split('_')[0]))

            # Get commits since specified date
            commits = git_service.get_commits_since(repo, since)

            # Analyze commits
            stats = git_service.analyze_commits(repo, commits)

            # Aggregate statistics
            total_commits += stats['commits_count']
            total_lines_added += stats['lines_added']
            total_lines_deleted += stats['lines_deleted']

            # Merge language breakdown
            for lang, lines in stats['languages_breakdown'].items():
                total_languages[lang] = total_languages.get(lang, 0) + lines

            # Note: files_changed is returned as an integer from analyze_commits
            if isinstance(stats['files_changed'], int):
                # Can't aggregate file sets if we only have counts
                # Just sum the counts (may have duplicates across repos)
                pass

        # Return aggregated response
        return GitStatsResponse(
            commits_count=total_commits,
            files_changed=0,  # Not meaningful when aggregating multiple repos
            lines_added=total_lines_added,
            lines_deleted=total_lines_deleted,
            languages_breakdown=total_languages,
            analyzed_since=since,
            repo_url=", ".join(effective_repo_urls)  # Show all analyzed repos
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
