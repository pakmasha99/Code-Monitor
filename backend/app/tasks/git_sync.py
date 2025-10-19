"""
Celery tasks for Git repository synchronization
"""
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from backend.app.core.celery_app import celery_app
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.git_metrics import GitMetrics
from backend.app.services.git_service import GitSyncService


def get_week_start_date(date: datetime) -> datetime:
    """Get Monday of the week for a given date"""
    return date - timedelta(days=date.weekday())


@celery_app.task(name='backend.app.tasks.git_sync.sync_user_repository')
def sync_user_repository(user_id: int) -> dict:
    """
    Sync a single user's repository and analyze commits.

    Args:
        user_id: User ID to sync

    Returns:
        Dict with sync results
    """
    db: Session = SessionLocal()
    git_service = GitSyncService()

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.repo_url:
            return {
                'status': 'skipped',
                'user_id': user_id,
                'reason': 'No repository URL configured'
            }

        # Clone or pull repository
        repo = git_service.clone_or_pull(user.repo_url, user_id)

        # Get current week start date
        now = datetime.utcnow()
        week_start = get_week_start_date(now).date()

        # Get commits since last sync (last week)
        since_date = now - timedelta(days=7)
        commits = git_service.get_commits_since(repo, since_date)

        # Analyze commits
        metrics = git_service.analyze_commits(repo, commits)

        # Check if metrics already exist for this week
        existing_metrics = db.query(GitMetrics).filter(
            GitMetrics.user_id == user_id,
            GitMetrics.week_start_date == week_start
        ).first()

        if existing_metrics:
            # Update existing metrics
            existing_metrics.commits_count = metrics['commits_count']
            existing_metrics.lines_added = metrics['lines_added']
            existing_metrics.lines_deleted = metrics['lines_deleted']
            existing_metrics.files_changed = metrics['files_changed']
            existing_metrics.languages_breakdown = metrics['languages_breakdown']
        else:
            # Create new metrics
            git_metrics = GitMetrics(
                user_id=user_id,
                week_start_date=week_start,
                commits_count=metrics['commits_count'],
                lines_added=metrics['lines_added'],
                lines_deleted=metrics['lines_deleted'],
                files_changed=metrics['files_changed'],
                languages_breakdown=metrics['languages_breakdown']
            )
            db.add(git_metrics)

        db.commit()

        return {
            'status': 'success',
            'user_id': user_id,
            'user_name': user.name,
            'week_start_date': week_start.isoformat(),
            'metrics': metrics
        }

    except Exception as e:
        db.rollback()
        return {
            'status': 'error',
            'user_id': user_id,
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name='backend.app.tasks.git_sync.sync_all_repositories')
def sync_all_repositories() -> dict:
    """
    Sync all users' repositories (scheduled daily via Celery Beat).

    Returns:
        Dict with summary of sync results
    """
    db: Session = SessionLocal()

    try:
        # Get all users with repository URLs
        users = db.query(User).filter(User.repo_url.isnot(None)).all()

        results = {
            'total_users': len(users),
            'success': 0,
            'skipped': 0,
            'errors': 0,
            'details': []
        }

        # Sync each user's repository
        for user in users:
            result = sync_user_repository.delay(user.id).get()

            results['details'].append(result)

            if result['status'] == 'success':
                results['success'] += 1
            elif result['status'] == 'skipped':
                results['skipped'] += 1
            else:
                results['errors'] += 1

        return results

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name='backend.app.tasks.git_sync.sync_all_repositories_async')
def sync_all_repositories_async() -> dict:
    """
    Sync all repositories asynchronously (parallel execution).
    Faster but uses more resources.

    Returns:
        Dict with task IDs for monitoring
    """
    db: Session = SessionLocal()

    try:
        # Get all users with repository URLs
        users = db.query(User).filter(User.repo_url.isnot(None)).all()

        # Dispatch tasks asynchronously
        task_ids = []
        for user in users:
            task = sync_user_repository.delay(user.id)
            task_ids.append({
                'user_id': user.id,
                'user_name': user.name,
                'task_id': task.id
            })

        return {
            'status': 'dispatched',
            'total_users': len(users),
            'tasks': task_ids
        }

    finally:
        db.close()
