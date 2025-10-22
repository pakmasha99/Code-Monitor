#!/usr/bin/env python3
"""
Check submissions to diagnose document_lines_added data
"""
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.weekly_submission import WeeklySubmission
from app.models.user import User

db = SessionLocal()

try:
    submissions = db.query(WeeklySubmission).join(User).all()

    print("📊 Weekly Submissions Summary\n")
    print(f"{'User':<20} {'Week':<12} {'Code':<10} {'Docs':<10} {'Total':<10}")
    print("=" * 70)

    for sub in submissions:
        user_name = sub.user.name if sub.user else "Unknown"
        week = sub.week_start_date.isoformat()
        code = sub.code_lines_added
        docs = sub.document_lines_added
        total = code + docs

        print(f"{user_name:<20} {week:<12} {code:<10} {docs:<10} {total:<10}")

    print("\n" + "=" * 70)
    print(f"\nTotal submissions: {len(submissions)}")

    # Check for missing document_lines_added
    missing_docs = sum(1 for s in submissions if s.document_lines_added == 0)
    print(f"Submissions with document_lines_added = 0: {missing_docs}")

    if missing_docs > 0:
        print("\n⚠️  Some submissions have document_lines_added = 0")
        print("   This could mean:")
        print("   1. User hasn't submitted document lines yet")
        print("   2. Migration added column but didn't populate existing data")
        print("   3. Need to manually update submissions with document line counts")

finally:
    db.close()
