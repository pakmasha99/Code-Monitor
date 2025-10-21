#!/usr/bin/env python3
"""
Initialize RAG index for all users with repositories

This script:
1. Finds all users with configured repo_url
2. Triggers reindexing for each user
3. Reports success/failure for each user

Usage:
    python scripts/init_rag_index.py
    python scripts/init_rag_index.py --user-id 1  # Index specific user only
"""
import sys
import os
import argparse
import requests
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User


def trigger_reindex(user_id: int, api_url: str = "http://localhost:8000") -> dict:
    """
    Trigger RAG reindexing for a user via API

    Args:
        user_id: User ID to reindex
        api_url: Base URL of FastAPI server

    Returns:
        Response dict from API
    """
    url = f"{api_url}/api/v1/rag/reindex"
    payload = {"user_id": user_id}

    try:
        response = requests.post(url, json=payload, timeout=300)  # 5 min timeout
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Initialize RAG index for users")
    parser.add_argument(
        "--user-id",
        type=int,
        help="Index specific user ID only (default: all users with repo_url)"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="FastAPI server URL (default: http://localhost:8000)"
    )
    args = parser.parse_args()

    db = SessionLocal()

    try:
        # Get users to index
        if args.user_id:
            users = db.query(User).filter(User.id == args.user_id).all()
            if not users:
                print(f"❌ User ID {args.user_id} not found")
                return 1
        else:
            # Get all users with repo_url configured
            users = db.query(User).filter(User.repo_url.isnot(None)).all()

        if not users:
            print("ℹ️  No users with configured repositories found")
            return 0

        print(f"🚀 Starting RAG indexing for {len(users)} user(s)...\n")

        success_count = 0
        failure_count = 0

        for user in users:
            print(f"📍 Processing user: {user.name} (ID: {user.id})")
            print(f"   Repository: {user.repo_url}")

            result = trigger_reindex(user.id, args.api_url)

            if result["success"]:
                print(f"   ✅ Success: {result['data'].get('message', 'Indexing queued')}")
                print(f"   Task ID: {result['data'].get('task_id', 'N/A')}\n")
                success_count += 1
            else:
                print(f"   ❌ Failed: {result['error']}\n")
                failure_count += 1

        # Summary
        print("=" * 60)
        print(f"✨ Indexing Summary:")
        print(f"   Total users: {len(users)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {failure_count}")
        print("=" * 60)

        if failure_count > 0:
            print("\n⚠️  Some indexing tasks failed. Check API logs for details.")
            return 1

        print("\n🎉 All indexing tasks queued successfully!")
        print("   Monitor Celery worker for progress:")
        print("   celery -A app.core.celery_app worker --loglevel=info")

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
