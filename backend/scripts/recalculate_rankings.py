#!/usr/bin/env python3
"""
Recalculate all rankings with new scoring formula

This script recalculates all rankings in the database using the new scoring formula:
Total Score = code_lines_added + document_lines_added

Usage:
    python scripts/recalculate_rankings.py
    python scripts/recalculate_rankings.py --week-start-date 2024-10-14  # Specific week only
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import date, timedelta

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.weekly_submission import WeeklySubmission
from app.services.ranking_service import RankingService


def get_all_submission_weeks(db) -> list[date]:
    """Get all unique week_start_date values from submissions"""
    weeks = db.query(WeeklySubmission.week_start_date).distinct().all()
    return sorted([w[0] for w in weeks])


def main():
    parser = argparse.ArgumentParser(description="Recalculate all rankings with new formula")
    parser.add_argument(
        "--week-start-date",
        type=str,
        help="Recalculate specific week only (YYYY-MM-DD format, must be Monday)"
    )
    args = parser.parse_args()

    db = SessionLocal()
    ranking_service = RankingService()

    try:
        # Determine which weeks to recalculate
        if args.week_start_date:
            weeks_to_process = [date.fromisoformat(args.week_start_date)]
            print(f"🎯 Recalculating rankings for week: {args.week_start_date}\n")
        else:
            weeks_to_process = get_all_submission_weeks(db)
            print(f"🎯 Recalculating rankings for {len(weeks_to_process)} weeks\n")

        if not weeks_to_process:
            print("ℹ️  No submissions found to recalculate")
            return 0

        success_count = 0
        failure_count = 0

        for week_start in weeks_to_process:
            print(f"📅 Processing week: {week_start.isoformat()}")

            try:
                # Recalculate rankings for this week
                result = ranking_service.update_weekly_rankings(week_start, db)

                print(f"   ✅ Success: {result['updated']} rankings updated")
                success_count += 1

            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
                failure_count += 1

        # Summary
        print("\n" + "=" * 60)
        print(f"✨ Recalculation Summary:")
        print(f"   Total weeks: {len(weeks_to_process)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {failure_count}")
        print("=" * 60)

        if failure_count > 0:
            print("\n⚠️  Some weeks failed to recalculate. Check error messages above.")
            return 1

        print("\n🎉 All rankings recalculated successfully!")
        print("   Rankings now use formula: Total Score = code_lines_added + document_lines_added")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
