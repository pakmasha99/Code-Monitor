"""
Tests for ranking calculation service (TDD)
"""
import pytest
from datetime import date, datetime, timedelta
from app.models.user import User, UserRole
from app.models.weekly_submission import WeeklySubmission
from app.models.git_metrics import GitMetrics
from app.models.ranking import Ranking


class TestRankingCalculation:
    """Test ranking score calculation logic"""

    def test_calculate_weekly_score_from_git_metrics(self, db_session, sample_user):
        """Test calculating weekly score from git metrics only"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Create git metrics
        git_metrics = GitMetrics(
            user_id=sample_user.id,
            week_start_date=week_start,
            commits_count=10,
            lines_added=500,
            lines_deleted=100,
            files_changed=15,
            languages_breakdown={"Python": 300, "JavaScript": 200}
        )
        db_session.add(git_metrics)
        db_session.commit()

        # Calculate score
        score = service.calculate_weekly_score(sample_user.id, week_start, db_session)

        assert score is not None
        assert score["total_score"] > 0
        assert "productivity" in score
        assert "quality" in score
        assert "consistency" in score

    def test_calculate_weekly_score_from_submission_only(self, db_session, sample_user):
        """Test calculating weekly score from manual submission only"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Create weekly submission
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=week_start,
            code_lines_added=400,
            documents_created=3,
            notes="Good week"
        )
        db_session.add(submission)
        db_session.commit()

        # Calculate score
        score = service.calculate_weekly_score(sample_user.id, week_start, db_session)

        assert score is not None
        assert score["total_score"] > 0
        assert score["productivity"] > 0

    def test_calculate_weekly_score_combined_data(self, db_session, sample_user):
        """Test calculating score from both git metrics and submission"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Create both git metrics and submission
        git_metrics = GitMetrics(
            user_id=sample_user.id,
            week_start_date=week_start,
            commits_count=10,
            lines_added=500,
            lines_deleted=100,
            files_changed=15
        )
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=week_start,
            code_lines_added=400,
            documents_created=3
        )
        db_session.add_all([git_metrics, submission])
        db_session.commit()

        # Calculate score
        score = service.calculate_weekly_score(sample_user.id, week_start, db_session)

        # Combined score should be higher than individual
        assert score["total_score"] > 0
        assert score["productivity"] > 0

    def test_calculate_score_no_data(self, db_session, sample_user):
        """Test calculating score when user has no data"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Calculate score with no data
        score = service.calculate_weekly_score(sample_user.id, week_start, db_session)

        assert score is not None
        assert score["total_score"] == 0
        assert score["productivity"] == 0
        assert score["quality"] == 0
        assert score["consistency"] == 0

    def test_productivity_score_components(self, db_session, sample_user):
        """Test that productivity score includes expected components"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

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

        score = service.calculate_weekly_score(sample_user.id, week_start, db_session)

        # Productivity should consider commits, lines, and files
        assert score["productivity"] > 0
        # More commits/lines should increase productivity
        assert score["total_score"] > 0

    def test_quality_score_from_code_ratio(self, db_session, sample_user):
        """Test quality score based on code deletion ratio"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # High quality: more additions, fewer deletions
        git_metrics = GitMetrics(
            user_id=sample_user.id,
            week_start_date=week_start,
            commits_count=10,
            lines_added=1000,
            lines_deleted=50,  # Low deletion ratio
            files_changed=15
        )
        db_session.add(git_metrics)
        db_session.commit()

        score = service.calculate_weekly_score(sample_user.id, week_start, db_session)

        assert score["quality"] > 0

    def test_consistency_score_from_commits(self, db_session, sample_user):
        """Test consistency score from regular commits"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Regular commits indicate consistency
        git_metrics = GitMetrics(
            user_id=sample_user.id,
            week_start_date=week_start,
            commits_count=10,  # Good number of commits
            lines_added=500,
            lines_deleted=100,
            files_changed=15
        )
        db_session.add(git_metrics)
        db_session.commit()

        score = service.calculate_weekly_score(sample_user.id, week_start, db_session)

        assert score["consistency"] > 0


class TestRankingGeneration:
    """Test ranking list generation"""

    def test_update_weekly_rankings_single_user(self, db_session, sample_user):
        """Test updating rankings for a single user week"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Create data for user
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

        # Update rankings
        results = service.update_weekly_rankings(week_start, db_session)

        assert results["total_users"] == 1
        assert results["updated"] == 1

        # Check ranking was created
        ranking = db_session.query(Ranking).filter(
            Ranking.user_id == sample_user.id,
            Ranking.week_start_date == week_start
        ).first()

        assert ranking is not None
        assert ranking.rank_position == 1
        assert ranking.total_score > 0

    def test_update_weekly_rankings_multiple_users(self, db_session):
        """Test ranking multiple users with different scores"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Create 3 users with different performance
        users = []
        for i in range(3):
            user = User(
                name=f"User {i+1}",
                email=f"user{i+1}@lab.com",
                role=UserRole.STUDENT
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()

        # User 1: High performer
        git1 = GitMetrics(
            user_id=users[0].id,
            week_start_date=week_start,
            commits_count=20,
            lines_added=1000,
            lines_deleted=50,
            files_changed=30
        )

        # User 2: Medium performer
        git2 = GitMetrics(
            user_id=users[1].id,
            week_start_date=week_start,
            commits_count=10,
            lines_added=500,
            lines_deleted=100,
            files_changed=15
        )

        # User 3: Low performer
        git3 = GitMetrics(
            user_id=users[2].id,
            week_start_date=week_start,
            commits_count=5,
            lines_added=200,
            lines_deleted=50,
            files_changed=8
        )

        db_session.add_all([git1, git2, git3])
        db_session.commit()

        # Update rankings
        results = service.update_weekly_rankings(week_start, db_session)

        assert results["updated"] == 3

        # Check rankings are correct
        rankings = db_session.query(Ranking).filter(
            Ranking.week_start_date == week_start
        ).order_by(Ranking.rank_position).all()

        assert len(rankings) == 3
        assert rankings[0].rank_position == 1  # Highest score
        assert rankings[1].rank_position == 2
        assert rankings[2].rank_position == 3  # Lowest score
        assert rankings[0].total_score > rankings[1].total_score
        assert rankings[1].total_score > rankings[2].total_score

    def test_update_rankings_handles_ties(self, db_session):
        """Test ranking handles users with equal scores"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Create 2 users with identical performance
        users = []
        for i in range(2):
            user = User(
                name=f"User {i+1}",
                email=f"user{i+1}@lab.com",
                role=UserRole.STUDENT
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()

        # Both users have same metrics
        for user in users:
            git = GitMetrics(
                user_id=user.id,
                week_start_date=week_start,
                commits_count=10,
                lines_added=500,
                lines_deleted=100,
                files_changed=15
            )
            db_session.add(git)
        db_session.commit()

        # Update rankings
        results = service.update_weekly_rankings(week_start, db_session)

        assert results["updated"] == 2

        # Check both have same rank
        rankings = db_session.query(Ranking).filter(
            Ranking.week_start_date == week_start
        ).all()

        assert len(rankings) == 2
        # Both should have rank 1 (or same rank)
        assert rankings[0].rank_position == rankings[1].rank_position

    def test_update_rankings_skips_users_without_data(self, db_session):
        """Test that users without data get rank 0 or are skipped"""
        from app.services.ranking_service import RankingService

        service = RankingService()
        week_start = date(2024, 1, 15)

        # Create user with no metrics
        user = User(
            name="Inactive User",
            email="inactive@lab.com",
            role=UserRole.STUDENT
        )
        db_session.add(user)
        db_session.commit()

        # Update rankings
        results = service.update_weekly_rankings(week_start, db_session)

        # Should either skip or create with 0 score
        ranking = db_session.query(Ranking).filter(
            Ranking.user_id == user.id,
            Ranking.week_start_date == week_start
        ).first()

        # Either no ranking or ranking with 0 score
        if ranking:
            assert ranking.total_score == 0


class TestRankingRetrieval:
    """Test retrieving and querying rankings"""

    def test_get_current_week_rankings(self, db_session):
        """Test getting rankings for current week"""
        from app.services.ranking_service import RankingService

        service = RankingService()

        # Get current week start
        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).date()

        # Create test data
        user = User(name="Test User", email="test@lab.com", role=UserRole.STUDENT)
        db_session.add(user)
        db_session.commit()

        ranking = Ranking(
            user_id=user.id,
            week_start_date=week_start,
            total_score=100.0,
            rank_position=1,
            category_scores={"productivity": 50, "quality": 30, "consistency": 20}
        )
        db_session.add(ranking)
        db_session.commit()

        # Get current week rankings
        rankings = service.get_weekly_rankings(week_start, db_session)

        assert len(rankings) > 0
        assert rankings[0]["rank_position"] == 1
        assert rankings[0]["total_score"] == 100.0

    def test_get_top_performers(self, db_session):
        """Test getting top N performers"""
        from app.services.ranking_service import RankingService

        service = RankingService()
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
                total_score=100.0 - (i * 10),  # Descending scores
                rank_position=i + 1,
                category_scores={}
            )
            db_session.add(ranking)
        db_session.commit()

        # Get top 3
        top_3 = service.get_top_performers(week_start, limit=3, db=db_session)

        assert len(top_3) == 3
        assert top_3[0]["rank_position"] == 1
        assert top_3[1]["rank_position"] == 2
        assert top_3[2]["rank_position"] == 3
