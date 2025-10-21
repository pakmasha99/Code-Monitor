"""
Tests for git stats API endpoints
"""
from datetime import datetime
from unittest.mock import Mock, patch
import pytest
from fastapi.testclient import TestClient
from git import GitCommandError

from app.models.user import User, UserRole


class TestGitStatsAPI:
    """Test git stats collection endpoint"""

    @patch('app.api.git_stats.GitSyncService')
    def test_get_git_stats_success(self, mock_git_service, client: TestClient, sample_user: User, db_session):
        """Test successfully fetching git stats from user's stored repo_url"""
        # Add repo_url to user
        sample_user.repo_url = "https://github.com/test_user/test_repo"
        db_session.commit()

        # Mock GitSyncService behavior
        mock_service_instance = Mock()
        mock_git_service.return_value = mock_service_instance

        mock_repo = Mock()
        mock_service_instance.clone_or_pull.return_value = mock_repo
        mock_service_instance.get_commits_since.return_value = [Mock(), Mock(), Mock()]
        mock_service_instance.analyze_commits.return_value = {
            'commits_count': 3,
            'files_changed': 15,
            'lines_added': 450,
            'lines_deleted': 120,
            'languages_breakdown': {'Python': 250, 'TypeScript': 200}
        }

        # Make request
        since_date = "2024-01-15T00:00:00"
        response = client.get(
            f"/api/users/{sample_user.id}/git-stats",
            params={"since": since_date}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["commits_count"] == 3
        assert data["files_changed"] == 15
        assert data["lines_added"] == 450
        assert data["lines_deleted"] == 120
        assert data["languages_breakdown"] == {'Python': 250, 'TypeScript': 200}
        assert data["analyzed_since"] == since_date
        assert data["repo_url"] == "https://github.com/test_user/test_repo"

    @patch('app.api.git_stats.GitSyncService')
    def test_get_git_stats_with_override_repo_url(
        self, mock_git_service, client: TestClient, sample_user: User
    ):
        """Test fetching git stats with provided repo_url parameter"""
        # User has no stored repo_url
        assert sample_user.repo_url is None

        # Mock GitSyncService
        mock_service_instance = Mock()
        mock_git_service.return_value = mock_service_instance

        mock_repo = Mock()
        mock_service_instance.clone_or_pull.return_value = mock_repo
        mock_service_instance.get_commits_since.return_value = [Mock()]
        mock_service_instance.analyze_commits.return_value = {
            'commits_count': 1,
            'files_changed': 5,
            'lines_added': 100,
            'lines_deleted': 20,
            'languages_breakdown': {'JavaScript': 100}
        }

        # Make request with repo_url parameter
        repo_url = "https://github.com/test_user/another_repo"
        response = client.get(
            f"/api/users/{sample_user.id}/git-stats",
            params={
                "since": "2024-01-15T00:00:00",
                "repo_url": repo_url
            }
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["commits_count"] == 1
        assert data["repo_url"] == repo_url

    def test_get_git_stats_user_not_found(self, client: TestClient):
        """Test 404 when user doesn't exist"""
        response = client.get(
            "/api/users/99999/git-stats",
            params={"since": "2024-01-15T00:00:00"}
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_git_stats_no_repo_url(self, client: TestClient, sample_user: User):
        """Test 400 when no repo_url is available"""
        # Ensure user has no repo_url
        assert sample_user.repo_url is None

        response = client.get(
            f"/api/users/{sample_user.id}/git-stats",
            params={"since": "2024-01-15T00:00:00"}
        )

        assert response.status_code == 400
        assert "No repository URL" in response.json()["detail"]

    def test_get_git_stats_invalid_date_format(
        self, client: TestClient, sample_user: User, db_session
    ):
        """Test 422 validation error for invalid date format"""
        sample_user.repo_url = "https://github.com/test_user/test_repo"
        db_session.commit()

        response = client.get(
            f"/api/users/{sample_user.id}/git-stats",
            params={"since": "invalid-date"}
        )

        assert response.status_code == 422  # Pydantic validation error

    @patch('app.api.git_stats.GitSyncService')
    def test_get_git_stats_git_clone_failure(
        self, mock_git_service, client: TestClient, sample_user: User, db_session
    ):
        """Test 500 when git clone/pull fails"""
        sample_user.repo_url = "https://github.com/test_user/test_repo"
        db_session.commit()

        # Mock git operation failure
        mock_service_instance = Mock()
        mock_git_service.return_value = mock_service_instance
        mock_service_instance.clone_or_pull.side_effect = GitCommandError(
            "git clone", "Repository not found"
        )

        response = client.get(
            f"/api/users/{sample_user.id}/git-stats",
            params={"since": "2024-01-15T00:00:00"}
        )

        assert response.status_code == 500
        assert "Git operation failed" in response.json()["detail"]

    @patch('app.api.git_stats.GitSyncService')
    def test_get_git_stats_empty_commits(
        self, mock_git_service, client: TestClient, sample_user: User, db_session
    ):
        """Test returns zeros when no commits found in date range"""
        sample_user.repo_url = "https://github.com/test_user/test_repo"
        db_session.commit()

        # Mock empty commits
        mock_service_instance = Mock()
        mock_git_service.return_value = mock_service_instance

        mock_repo = Mock()
        mock_service_instance.clone_or_pull.return_value = mock_repo
        mock_service_instance.get_commits_since.return_value = []  # No commits
        mock_service_instance.analyze_commits.return_value = {
            'commits_count': 0,
            'files_changed': 0,
            'lines_added': 0,
            'lines_deleted': 0,
            'languages_breakdown': {}
        }

        response = client.get(
            f"/api/users/{sample_user.id}/git-stats",
            params={"since": "2024-01-15T00:00:00"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["commits_count"] == 0
        assert data["lines_added"] == 0
        assert data["lines_deleted"] == 0
        assert data["languages_breakdown"] == {}

    @patch('app.api.git_stats.GitSyncService')
    def test_get_git_stats_invalid_repo_url(
        self, mock_git_service, client: TestClient, sample_user: User
    ):
        """Test 400 when repo_url format is invalid"""
        # Try with non-GitHub URL
        response = client.get(
            f"/api/users/{sample_user.id}/git-stats",
            params={
                "since": "2024-01-15T00:00:00",
                "repo_url": "https://malicious-site.com/repo"
            }
        )

        assert response.status_code == 400
        assert "Only GitHub URLs are allowed" in response.json()["detail"]

    @patch('app.api.git_stats.GitSyncService')
    def test_get_git_stats_current_week(
        self, mock_git_service, client: TestClient, sample_user: User, db_session
    ):
        """Test fetching stats for current week (realistic use case)"""
        sample_user.repo_url = "https://github.com/test_user/test_repo"
        db_session.commit()

        # Mock GitSyncService
        mock_service_instance = Mock()
        mock_git_service.return_value = mock_service_instance

        mock_repo = Mock()
        mock_service_instance.clone_or_pull.return_value = mock_repo
        mock_service_instance.get_commits_since.return_value = [Mock(), Mock()]
        mock_service_instance.analyze_commits.return_value = {
            'commits_count': 2,
            'files_changed': 10,
            'lines_added': 850,
            'lines_deleted': 50,
            'languages_breakdown': {'Python': 500, 'TypeScript': 350}
        }

        # Calculate current week Monday
        now = datetime.utcnow()
        days_since_monday = now.weekday()
        from datetime import timedelta
        current_week_monday = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        response = client.get(
            f"/api/users/{sample_user.id}/git-stats",
            params={"since": current_week_monday.isoformat()}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["commits_count"] == 2
        assert data["lines_added"] == 850
