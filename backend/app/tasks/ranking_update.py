"""
Celery tasks for ranking updates
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.ranking_service import RankingService


@celery_app.task(name='app.tasks.ranking_update.update_current_week_rankings')
def update_current_week_rankings() -> dict:
    """
    Update rankings for the current week (scheduled weekly).

    Returns:
        Dict with update results
    """
    db: Session = SessionLocal()
    service = RankingService()

    try:
        # Get current week start (Monday)
        week_start = service.get_current_week_start()

        # Update rankings
        result = service.update_weekly_rankings(week_start, db)

        print(f"✅ Updated rankings for week {week_start}: {result['updated']} users")

        return {
            'status': 'success',
            **result
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error updating rankings: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.ranking_update.update_specific_week_rankings')
def update_specific_week_rankings(week_start_date: str) -> dict:
    """
    Update rankings for a specific week.

    Args:
        week_start_date: Week start date in YYYY-MM-DD format

    Returns:
        Dict with update results
    """
    db: Session = SessionLocal()
    service = RankingService()

    try:
        from datetime import date
        week_start = date.fromisoformat(week_start_date)

        # Update rankings
        result = service.update_weekly_rankings(week_start, db)

        print(f"✅ Updated rankings for week {week_start}: {result['updated']} users")

        return {
            'status': 'success',
            **result
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error updating rankings for {week_start_date}: {e}")
        return {
            'status': 'error',
            'week_start_date': week_start_date,
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name='app.tasks.ranking_update.backfill_rankings')
def backfill_rankings(weeks: int = 4) -> dict:
    """
    Backfill rankings for the past N weeks.

    Useful for:
    - Initial system setup
    - Recovering from missed updates
    - Historical data generation

    Args:
        weeks: Number of weeks to backfill (default 4)

    Returns:
        Dict with backfill results
    """
    db: Session = SessionLocal()
    service = RankingService()

    try:
        now = datetime.utcnow()
        current_week_start = service.get_current_week_start()

        results = []
        for i in range(weeks):
            week_start = current_week_start - timedelta(weeks=i)
            result = service.update_weekly_rankings(week_start, db)
            results.append({
                'week': week_start.isoformat(),
                'updated': result['updated']
            })

        total_updated = sum(r['updated'] for r in results)

        print(f"✅ Backfilled {weeks} weeks: {total_updated} total updates")

        return {
            'status': 'success',
            'weeks_processed': weeks,
            'total_updated': total_updated,
            'results': results
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error backfilling rankings: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        db.close()
