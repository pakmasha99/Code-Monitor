#!/usr/bin/env python3
"""
Verification script for new line-based scoring system.

Tests:
1. Score calculation formula: code_lines_added + (documents_created × 100)
2. Real-time ranking updates after submission
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.ranking_service import RankingService
from app.models.weekly_submission import WeeklySubmission
from app.models.ranking import Ranking
from datetime import datetime, timedelta


def get_week_start_date():
    """Get Monday of current week"""
    now = datetime.utcnow()
    return (now - timedelta(days=now.weekday())).date()


def verify_score_calculation():
    """Verify the scoring formula works correctly"""
    print("=" * 60)
    print("SCORING VERIFICATION TEST")
    print("=" * 60)
    print()

    db = SessionLocal()
    ranking_service = RankingService()
    week_start = get_week_start_date()

    try:
        # Get all submissions for current week
        submissions = db.query(WeeklySubmission).filter(
            WeeklySubmission.week_start_date == week_start
        ).all()

        if not submissions:
            print("⚠️  No submissions found for current week")
            print(f"Week start date: {week_start}")
            return

        print(f"Found {len(submissions)} submission(s) for week {week_start}")
        print()

        for submission in submissions:
            # Calculate expected score manually
            expected_score = (
                submission.code_lines_added +
                (submission.documents_created * ranking_service.LINES_PER_DOCUMENT)
            )

            # Get calculated score from service
            score_data = ranking_service.calculate_weekly_score(
                submission.user_id,
                week_start,
                db
            )

            # Get ranking from database
            ranking = db.query(Ranking).filter(
                Ranking.user_id == submission.user_id,
                Ranking.week_start_date == week_start
            ).first()

            print(f"User ID: {submission.user_id}")
            print(f"  Code Lines Added: {submission.code_lines_added:,}")
            print(f"  Documents Created: {submission.documents_created}")
            print(f"  Documents as Lines: {submission.documents_created * ranking_service.LINES_PER_DOCUMENT:,}")
            print(f"  Expected Score: {expected_score:,} lines")
            print(f"  Calculated Score: {score_data['total_score']:,} lines")

            if ranking:
                print(f"  DB Ranking Score: {ranking.total_score:,} lines")
                print(f"  Rank Position: #{ranking.rank_position}")

                # Verify scores match
                if abs(ranking.total_score - expected_score) < 0.01:
                    print("  ✅ Score matches expected value!")
                else:
                    print(f"  ❌ Score mismatch! Expected {expected_score}, got {ranking.total_score}")
            else:
                print("  ⚠️  No ranking entry found in database")

            print()

        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Formula: code_lines + (documents × {ranking_service.LINES_PER_DOCUMENT})")
        print(f"Unit: Lines (not points)")
        print("Real-time updates: Triggered on submission create/update")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    verify_score_calculation()
