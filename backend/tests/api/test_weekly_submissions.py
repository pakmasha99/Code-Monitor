"""
Tests for weekly submission API endpoints
"""
from datetime import date, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.user import User, UserRole
from backend.app.models.weekly_submission import WeeklySubmission


class TestWeeklySubmissionAPI:
    """Test weekly submission CRUD operations"""

    def test_create_weekly_submission(self, client: TestClient, sample_user: User):
        """Test creating a new weekly submission"""
        week_start = date(2024, 1, 15)  # A Monday
        response = client.post(
            f"/api/users/{sample_user.id}/submissions",
            json={
                "week_start_date": week_start.isoformat(),
                "code_lines_added": 450,
                "documents_created": 3,
                "notes": "Implemented auth system"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == sample_user.id
        assert data["code_lines_added"] == 450
        assert data["documents_created"] == 3
        assert data["notes"] == "Implemented auth system"

    def test_create_submission_for_nonexistent_user(self, client: TestClient):
        """Test creating submission for user that doesn't exist"""
        response = client.post(
            "/api/users/99999/submissions",
            json={
                "week_start_date": "2024-01-15",
                "code_lines_added": 100,
                "documents_created": 1
            }
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_create_duplicate_submission_same_week(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test that duplicate submissions for the same week are rejected"""
        week_start = date(2024, 1, 15)

        # Create first submission
        submission1 = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=week_start,
            code_lines_added=100,
            documents_created=1
        )
        db_session.add(submission1)
        db_session.commit()

        # Try to create duplicate
        response = client.post(
            f"/api/users/{sample_user.id}/submissions",
            json={
                "week_start_date": week_start.isoformat(),
                "code_lines_added": 200,
                "documents_created": 2
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_get_user_submissions(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test retrieving all submissions for a user"""
        # Create multiple submissions
        submissions = [
            WeeklySubmission(
                user_id=sample_user.id,
                week_start_date=date(2024, 1, 15),
                code_lines_added=100,
                documents_created=1
            ),
            WeeklySubmission(
                user_id=sample_user.id,
                week_start_date=date(2024, 1, 22),
                code_lines_added=200,
                documents_created=2
            ),
            WeeklySubmission(
                user_id=sample_user.id,
                week_start_date=date(2024, 1, 29),
                code_lines_added=150,
                documents_created=1
            )
        ]
        db_session.add_all(submissions)
        db_session.commit()

        response = client.get(f"/api/users/{sample_user.id}/submissions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by date descending
        assert data[0]["week_start_date"] == "2024-01-29"
        assert data[1]["week_start_date"] == "2024-01-22"
        assert data[2]["week_start_date"] == "2024-01-15"

    def test_get_all_submissions(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test retrieving all submissions across users"""
        # Create another user
        user2 = User(
            name="이영희",
            email="user2@lab.com",
            role=UserRole.STUDENT
        )
        db_session.add(user2)
        db_session.commit()

        # Create submissions for both users
        week_start = date(2024, 1, 15)
        submissions = [
            WeeklySubmission(
                user_id=sample_user.id,
                week_start_date=week_start,
                code_lines_added=100,
                documents_created=1
            ),
            WeeklySubmission(
                user_id=user2.id,
                week_start_date=week_start,
                code_lines_added=200,
                documents_created=2
            )
        ]
        db_session.add_all(submissions)
        db_session.commit()

        response = client.get("/api/submissions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Check user info is included
        assert "user_name" in data[0]
        assert "user_email" in data[0]

    def test_get_submissions_filtered_by_week(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test filtering submissions by week"""
        # Create submissions for different weeks
        submissions = [
            WeeklySubmission(
                user_id=sample_user.id,
                week_start_date=date(2024, 1, 15),
                code_lines_added=100,
                documents_created=1
            ),
            WeeklySubmission(
                user_id=sample_user.id,
                week_start_date=date(2024, 1, 22),
                code_lines_added=200,
                documents_created=2
            )
        ]
        db_session.add_all(submissions)
        db_session.commit()

        response = client.get("/api/submissions?week_start_date=2024-01-15")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["week_start_date"] == "2024-01-15"

    def test_get_specific_submission(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test retrieving a specific submission by ID"""
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2024, 1, 15),
            code_lines_added=100,
            documents_created=1,
            notes="Test submission"
        )
        db_session.add(submission)
        db_session.commit()

        response = client.get(
            f"/api/users/{sample_user.id}/submissions/{submission.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == submission.id
        assert data["notes"] == "Test submission"

    def test_get_nonexistent_submission(self, client: TestClient, sample_user: User):
        """Test retrieving a submission that doesn't exist"""
        response = client.get(f"/api/users/{sample_user.id}/submissions/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_submission(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test updating a weekly submission"""
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2024, 1, 15),
            code_lines_added=100,
            documents_created=1,
            notes="Original notes"
        )
        db_session.add(submission)
        db_session.commit()

        response = client.patch(
            f"/api/users/{sample_user.id}/submissions/{submission.id}",
            json={
                "code_lines_added": 150,
                "notes": "Updated notes"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code_lines_added"] == 150
        assert data["notes"] == "Updated notes"
        # documents_created should remain unchanged
        assert data["documents_created"] == 1

    def test_delete_submission(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test deleting a weekly submission"""
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2024, 1, 15),
            code_lines_added=100,
            documents_created=1
        )
        db_session.add(submission)
        db_session.commit()
        submission_id = submission.id

        response = client.delete(
            f"/api/users/{sample_user.id}/submissions/{submission_id}"
        )

        assert response.status_code == 204

        # Verify deletion
        db_session.expire_all()
        deleted = db_session.query(WeeklySubmission).filter(
            WeeklySubmission.id == submission_id
        ).first()
        assert deleted is None

    def test_get_current_week_submissions(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test getting submissions for the current week"""
        # Get current week start (Monday)
        now = datetime.utcnow()
        days_since_monday = now.weekday()
        current_week_start = (now - timedelta(days=days_since_monday)).date()

        # Create submission for current week
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=current_week_start,
            code_lines_added=100,
            documents_created=1
        )
        db_session.add(submission)
        db_session.commit()

        response = client.get("/api/submissions/current-week")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["week_start_date"] == current_week_start.isoformat()
        assert "user_name" in data[0]

    def test_negative_values_rejected(self, client: TestClient, sample_user: User):
        """Test that negative values are rejected"""
        response = client.post(
            f"/api/users/{sample_user.id}/submissions",
            json={
                "week_start_date": "2024-01-15",
                "code_lines_added": -100,  # Invalid
                "documents_created": 1
            }
        )

        assert response.status_code == 422  # Validation error
