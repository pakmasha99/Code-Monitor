"""
Tests for rankings API endpoints (TDD)
"""
import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from app.models.user import User, UserRole
from app.models.git_metrics import GitMetrics
from app.models.ranking import Ranking


class TestRankingsAPI:
    """Test rankings API endpoints"""

    def test_get_current_week_rankings(self, client: TestClient, db_session):
        """Test getting current week rankings"""
        # Create users and rankings
        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).date()

        user1 = User(name="Top User", email="top@lab.com", role=UserRole.STUDENT)
        user2 = User(name="Second User", email="second@lab.com", role=UserRole.STUDENT)
        db_session.add_all([user1, user2])
        db_session.commit()

        # Create rankings
        ranking1 = Ranking(
            user_id=user1.id,
            week_start_date=week_start,
            total_score=100.0,
            rank_position=1,
            category_scores={"productivity": 50, "quality": 30, "consistency": 20}
        )
        ranking2 = Ranking(
            user_id=user2.id,
            week_start_date=week_start,
            total_score=80.0,
            rank_position=2,
            category_scores={"productivity": 40, "quality": 25, "consistency": 15}
        )
        db_session.add_all([ranking1, ranking2])
        db_session.commit()

        # Get current week rankings
        response = client.get("/api/rankings/current")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["rank_position"] == 1
        assert data[0]["user_name"] == "Top User"
        assert data[0]["total_score"] == 100.0
        assert data[1]["rank_position"] == 2

    def test_get_specific_week_rankings(self, client: TestClient, db_session):
        """Test getting rankings for a specific week"""
        week_start = date(2024, 1, 15)

        user = User(name="Test User", email="test@lab.com", role=UserRole.STUDENT)
        db_session.add(user)
        db_session.commit()

        ranking = Ranking(
            user_id=user.id,
            week_start_date=week_start,
            total_score=90.0,
            rank_position=1,
            category_scores={}
        )
        db_session.add(ranking)
        db_session.commit()

        # Get specific week rankings
        response = client.get(f"/api/rankings/week/{week_start.isoformat()}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["week_start_date"] == week_start.isoformat()
        assert data[0]["total_score"] == 90.0

    def test_get_top_performers(self, client: TestClient, db_session):
        """Test getting top N performers"""
        week_start = date(2024, 1, 15)

        # Create 5 users with different ranks
        for i in range(5):
            user = User(
                name=f"User {i+1}",
                email=f"user{i+1}@lab.com",
                role=UserRole.STUDENT
            )
            db_session.add(user)
            db_session.commit()

            ranking = Ranking(
                user_id=user.id,
                week_start_date=week_start,
                total_score=100.0 - (i * 10),
                rank_position=i + 1,
                category_scores={}
            )
            db_session.add(ranking)
        db_session.commit()

        # Get top 3
        response = client.get(f"/api/rankings/top/3?week_start_date={week_start.isoformat()}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["rank_position"] == 1
        assert data[1]["rank_position"] == 2
        assert data[2]["rank_position"] == 3

    def test_get_user_ranking_history(self, client: TestClient, db_session):
        """Test getting user's ranking history"""
        user = User(name="Test User", email="test@lab.com", role=UserRole.STUDENT)
        db_session.add(user)
        db_session.commit()

        # Create rankings for 3 weeks (current and previous weeks)
        now = datetime.utcnow()
        current_week_start = (now - timedelta(days=now.weekday())).date()

        for i in range(3):
            week_start = current_week_start - timedelta(weeks=i)
            ranking = Ranking(
                user_id=user.id,
                week_start_date=week_start,
                total_score=80.0 + (i * 5),
                rank_position=i + 1,
                category_scores={}
            )
            db_session.add(ranking)
        db_session.commit()

        # Get history
        response = client.get(f"/api/users/{user.id}/ranking/history?weeks=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by date descending (most recent first)
        assert data[0]["week_start_date"] == current_week_start.isoformat()
        assert data[1]["week_start_date"] == (current_week_start - timedelta(weeks=1)).isoformat()
        assert data[2]["week_start_date"] == (current_week_start - timedelta(weeks=2)).isoformat()

    def test_trigger_ranking_update(self, client: TestClient, db_session, sample_user):
        """Test triggering manual ranking update"""
        week_start = date(2024, 1, 15)

        # Create git metrics
        git_metrics = GitMetrics(
            user_id=sample_user.id,
            week_start_date=week_start,
            commits_count=10,
            lines_added=500,
            lines_deleted=100,
            files_changed=15
        )
        db_session.add(git_metrics)
        db_session.commit()

        # Trigger update
        response = client.post(f"/api/rankings/update/{week_start.isoformat()}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["updated"] >= 1

        # Verify ranking was created
        ranking = db_session.query(Ranking).filter(
            Ranking.user_id == sample_user.id,
            Ranking.week_start_date == week_start
        ).first()

        assert ranking is not None
        assert ranking.total_score > 0

    def test_get_rankings_empty_week(self, client: TestClient):
        """Test getting rankings for a week with no data"""
        week_start = date(2024, 1, 15)

        response = client.get(f"/api/rankings/week/{week_start.isoformat()}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_user_history_no_data(self, client: TestClient, sample_user):
        """Test getting history for user with no rankings"""
        response = client.get(f"/api/users/{sample_user.id}/ranking/history?weeks=4")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_user_history_nonexistent_user(self, client: TestClient):
        """Test getting history for non-existent user"""
        response = client.get("/api/users/99999/ranking/history?weeks=4")

        assert response.status_code == 404

    def test_invalid_week_date_format(self, client: TestClient):
        """Test invalid date format in week parameter"""
        response = client.get("/api/rankings/week/invalid-date")

        assert response.status_code == 422  # Validation error

    def test_rankings_include_all_categories(self, client: TestClient, db_session):
        """Test that rankings include all category scores"""
        week_start = date(2024, 1, 15)

        user = User(name="Test User", email="test@lab.com", role=UserRole.STUDENT)
        db_session.add(user)
        db_session.commit()

        ranking = Ranking(
            user_id=user.id,
            week_start_date=week_start,
            total_score=90.0,
            rank_position=1,
            category_scores={
                "productivity": 50.0,
                "quality": 25.0,
                "consistency": 15.0
            }
        )
        db_session.add(ranking)
        db_session.commit()

        response = client.get(f"/api/rankings/week/{week_start.isoformat()}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "category_scores" in data[0]
        assert data[0]["category_scores"]["productivity"] == 50.0
        assert data[0]["category_scores"]["quality"] == 25.0
        assert data[0]["category_scores"]["consistency"] == 15.0
