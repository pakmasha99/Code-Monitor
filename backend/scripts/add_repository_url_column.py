#!/usr/bin/env python3
"""
Migration script to add repository_url column to weekly_submissions table.

This migration adds support for custom repository URLs per submission,
allowing users to specify different repositories (e.g., team projects)
for specific weekly submissions.

Run this script once before deploying the new feature.
Can be run multiple times safely (idempotent).
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.database import engine


def is_sqlite() -> bool:
    """Detect if we're using SQLite."""
    return engine.url.drivername == 'sqlite'


def check_column_exists() -> bool:
    """Check if repository_url column already exists in weekly_submissions table."""
    with engine.connect() as conn:
        if is_sqlite():
            # SQLite: query pragma_table_info
            result = conn.execute(text("PRAGMA table_info(weekly_submissions);"))
            columns = [row[1] for row in result]
            return 'repository_url' in columns
        else:
            # PostgreSQL: query information_schema
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'weekly_submissions'
                    AND column_name = 'repository_url'
                );
            """))
            return result.scalar()


def add_repository_url_column():
    """Add repository_url column to weekly_submissions table if it doesn't exist."""

    print("🔍 Checking if repository_url column exists...")
    print(f"   Database: {'SQLite' if is_sqlite() else 'PostgreSQL'}")

    if check_column_exists():
        print("✅ Column 'repository_url' already exists in weekly_submissions table")
        print("   Migration is up to date - no changes needed")
        return

    print("➕ Adding repository_url column to weekly_submissions table...")

    with engine.begin() as conn:
        # Add the column - compatible with both SQLite and PostgreSQL
        conn.execute(text("""
            ALTER TABLE weekly_submissions
            ADD COLUMN repository_url VARCHAR(500);
        """))

        print("✅ Successfully added repository_url column")
        print("   Column details:")
        print("   - Name: repository_url")
        print("   - Type: VARCHAR(500)")
        print("   - Nullable: YES (implicit)")
        print("   - Default: NULL")

        # Add comment only for PostgreSQL
        if not is_sqlite():
            conn.execute(text("""
                COMMENT ON COLUMN weekly_submissions.repository_url IS
                'The actual repository URL used for this submission (either user default or custom)';
            """))
            print("✅ Added column comment for documentation")


def main():
    """Main migration execution."""
    print("=" * 60)
    print("Migration: Add repository_url to weekly_submissions")
    print("=" * 60)
    print()

    try:
        add_repository_url_column()
        print()
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Migration failed: {str(e)}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
