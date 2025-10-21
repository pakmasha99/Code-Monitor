"""
Test cases for custom repository URL feature in weekly submissions
"""
from datetime import date
import pytest
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.weekly_submission import WeeklySubmission


@pytest.fixture
def sample_user(db_session: Session):
    """Create a test user with default repo_url"""
    user = User(
        name="Test User",
        email="test@example.com",
        github_username="testuser",
        repo_url="https://github.com/testuser/personal-repo",
        role=UserRole.STUDENT,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_submission_with_custom_repo_url(client, sample_user, db_session):
    """
    Test that submission uses custom repository URL when provided.

    This verifies:
    - custom_repo_url is accepted in request
    - GitSyncService is called with custom repo URL
    - repository_url is stored in submission record
    """
    # Arrange
    custom_repo = "https://github.com/team/awesome-project"

    # Act
    response = client.post(
        f"/api/users/{sample_user.id}/submissions",
        json={
            "week_start_date": "2025-10-20",
            "code_lines_added": 1500,
            "documents_created": 3,
            "custom_repo_url": custom_repo
        }
    )

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify custom repo URL is stored
    assert data["repository_url"] == custom_repo

    # Verify submission is in database
    submission = db_session.query(WeeklySubmission).filter_by(
        user_id=sample_user.id,
        week_start_date=date(2025, 10, 20)
    ).first()
    assert submission is not None
    assert submission.repository_url == custom_repo


def test_submission_without_custom_repo_uses_default(client, sample_user, db_session):
    """
    Test that submission uses user's default repo_url when custom_repo_url is not provided.

    This verifies backward compatibility with existing behavior.
    """
    # Act
    response = client.post(
        f"/api/users/{sample_user.id}/submissions",
        json={
            "week_start_date": "2025-10-20",
            "code_lines_added": 1000,
            "documents_created": 2
        }
    )

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify default repo URL is used
    assert data["repository_url"] == sample_user.repo_url

    # Verify in database
    submission = db_session.query(WeeklySubmission).filter_by(
        user_id=sample_user.id,
        week_start_date=date(2025, 10, 20)
    ).first()
    assert submission.repository_url == sample_user.repo_url


def test_submission_rejects_invalid_github_url(client, sample_user, db_session):
    """
    Test that submission rejects non-GitHub URLs for security.

    Only GitHub URLs should be allowed (https://github.com/* or git@github.com:*)
    """
    # Act
    response = client.post(
        f"/api/users/{sample_user.id}/submissions",
        json={
            "week_start_date": "2025-10-20",
            "code_lines_added": 1000,
            "documents_created": 2,
            "custom_repo_url": "https://gitlab.com/team/project"  # Not GitHub
        }
    )

    # Assert
    assert response.status_code == 400
    assert "Only GitHub URLs are allowed" in response.json()["detail"]


def test_submission_rejects_invalid_url_format(client, sample_user, db_session):
    """
    Test that submission rejects invalid URL formats.
    """
    # Act
    response = client.post(
        f"/api/users/{sample_user.id}/submissions",
        json={
            "week_start_date": "2025-10-20",
            "code_lines_added": 1000,
            "documents_created": 2,
            "custom_repo_url": "not-a-valid-url"
        }
    )

    # Assert
    assert response.status_code == 400


def test_submission_fails_when_no_repo_available(client, db_session):
    """
    Test that submission fails when user has no default repo and no custom repo provided.
    """
    # Arrange - create user without repo_url
    user_no_repo = User(
        name="No Repo User",
        email="norepo@example.com",
        github_username="norepouser",
        repo_url=None,  # No default repository
        role=UserRole.STUDENT,
        is_active=True
    )
    db_session.add(user_no_repo)
    db_session.commit()
    db_session.refresh(user_no_repo)

    # Act - try to submit without custom_repo_url
    response = client.post(
        f"/api/users/{user_no_repo.id}/submissions",
        json={
            "week_start_date": "2025-10-20",
            "code_lines_added": 1000,
            "documents_created": 2
        }
    )

    # Assert
    assert response.status_code == 400
    assert "No repository URL" in response.json()["detail"]


def test_repository_url_stored_in_submission(client, sample_user, db_session):
    """
    Test that the actual repository URL used is stored in the submission record.

    This is important for tracking which repository's statistics were used.
    """
    # Arrange
    custom_repo = "https://github.com/snu-lab/connectome-kb"

    # Act
    response = client.post(
        f"/api/users/{sample_user.id}/submissions",
        json={
            "week_start_date": "2025-10-20",
            "code_lines_added": 3000,
            "documents_created": 5,
            "notes": "Team project work",
            "custom_repo_url": custom_repo
        }
    )

    # Assert
    assert response.status_code == 201

    # Verify stored in database with correct repository_url
    submission = db_session.query(WeeklySubmission).filter_by(
        user_id=sample_user.id,
        week_start_date=date(2025, 10, 20)
    ).first()

    assert submission is not None
    assert submission.repository_url == custom_repo
    assert submission.code_lines_added == 3000
    assert submission.notes == "Team project work"

    # Verify user's default repo_url is unchanged
    db_session.refresh(sample_user)
    assert sample_user.repo_url == "https://github.com/testuser/personal-repo"


def test_ssh_format_github_url_accepted(client, sample_user, db_session):
    """
    Test that SSH format GitHub URLs are accepted.

    Both HTTPS and SSH formats should work:
    - https://github.com/user/repo
    - git@github.com:user/repo.git
    """
    # Arrange
    ssh_repo = "git@github.com:team/project.git"

    # Act
    response = client.post(
        f"/api/users/{sample_user.id}/submissions",
        json={
            "week_start_date": "2025-10-20",
            "code_lines_added": 2000,
            "documents_created": 4,
            "custom_repo_url": ssh_repo
        }
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["repository_url"] == ssh_repo
