"""
Celery application configuration
"""
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "code_monitor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.git_sync', 'app.tasks.ranking_update', 'app.tasks.rag_indexing']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks (Beat schedule)
celery_app.conf.beat_schedule = {
    'sync-all-repos-daily': {
        'task': 'app.tasks.git_sync.sync_all_repositories',
        'schedule': 86400.0,  # Every 24 hours
    },
    'update-rankings-weekly': {
        'task': 'app.tasks.ranking_update.update_current_week_rankings',
        'schedule': 604800.0,  # Every 7 days (weekly)
    },
    'reindex-code-daily': {
        'task': 'app.tasks.rag_indexing.reindex_all_repositories',
        'schedule': 86400.0,  # Every 24 hours (after git sync)
    },
}
