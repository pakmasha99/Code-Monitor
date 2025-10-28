#!/usr/bin/env python
"""
Seed lab members data into the database
"""
import sys
import json
from pathlib import Path
from datetime import date

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.models.user import User, UserRole


def load_members_from_json(json_path: Path):
    """Load lab members from JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def seed_members():
    """Seed lab members into the database"""
    db = SessionLocal()

    try:
        # Load members data
        data_path = Path(__file__).parent.parent / "data" / "lab_members.json"
        members_data = load_members_from_json(data_path)

        print(f"📊 Loading {len(members_data)} lab members...")

        for member_data in members_data:
            # Check if user already exists
            existing_user = db.query(User).filter(
                User.email == member_data['email']
            ).first()

            if existing_user:
                print(f"⚠️  User {member_data['name']} ({member_data['email']}) already exists, skipping...")
                continue

            # Create new user
            user = User(
                name=member_data['name'],
                email=member_data['email'],
                github_username=member_data.get('github_username'),
                repo_url=member_data.get('repo_url'),
                role=UserRole(member_data.get('role', 'student')),
                is_active=member_data.get('is_active', True),
                joined_date=date.today()
            )

            db.add(user)
            print(f"✅ Added: {user.name} ({user.email})")

        db.commit()
        print("\n🎉 Lab members seeded successfully!")

    except FileNotFoundError:
        print(f"❌ Error: Could not find lab_members.json at {data_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_members()
