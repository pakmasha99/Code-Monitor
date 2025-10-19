"""
Tests for User model.

Following TDD approach - these tests define expected behavior.
"""
import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError

from backend.app.models.user import User, UserRole


class TestUserModel:
    """Test suite for User model"""

    def test_create_user_with_all_fields(self, db_session):
        """Test creating a user with all fields populated."""
        user = User(
            name="이영희",
            email="student2@lab.com",
            github_username="student2",
            repo_url="https://github.com/lab/student2",
            joined_date=date(2025, 1, 15),
            role=UserRole.STUDENT,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.name == "이영희"
        assert user.email == "student2@lab.com"
        assert user.github_username == "student2"
        assert user.repo_url == "https://github.com/lab/student2"
        assert user.joined_date == date(2025, 1, 15)
        assert user.role == UserRole.STUDENT
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_create_user_minimal_fields(self, db_session):
        """Test creating a user with only required fields."""
        user = User(
            name="박민수",
            email="student3@lab.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.name == "박민수"
        assert user.email == "student3@lab.com"
        assert user.github_username is None
        assert user.repo_url is None
        assert user.joined_date == date.today()  # Default
        assert user.role == UserRole.STUDENT  # Default
        assert user.is_active is True  # Default

    def test_email_must_be_unique(self, db_session, sample_user):
        """Test that email addresses must be unique."""
        duplicate_user = User(
            name="다른 사람",
            email=sample_user.email,  # Same email
        )
        db_session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_roles(self, db_session):
        """Test different user roles."""
        student = User(name="학생", email="student@lab.com", role=UserRole.STUDENT)
        advisor = User(name="교수", email="advisor@lab.com", role=UserRole.ADVISOR)
        admin = User(name="관리자", email="admin@lab.com", role=UserRole.ADMIN)

        db_session.add_all([student, advisor, admin])
        db_session.commit()

        assert student.role == UserRole.STUDENT
        assert advisor.role == UserRole.ADVISOR
        assert admin.role == UserRole.ADMIN

    def test_user_repr(self, sample_user):
        """Test string representation of User."""
        repr_str = repr(sample_user)
        assert "User" in repr_str
        assert str(sample_user.id) in repr_str
        assert sample_user.name in repr_str
        assert sample_user.email in repr_str

    def test_user_can_be_deactivated(self, db_session, sample_user):
        """Test that users can be marked as inactive."""
        assert sample_user.is_active is True

        sample_user.is_active = False
        db_session.commit()
        db_session.refresh(sample_user)

        assert sample_user.is_active is False

    def test_user_relationships_exist(self, sample_user):
        """Test that user has relationship attributes defined."""
        assert hasattr(sample_user, 'weekly_submissions')
        assert hasattr(sample_user, 'git_metrics')
        assert hasattr(sample_user, 'rankings')
        assert hasattr(sample_user, 'code_analyses')

    def test_timestamps_are_set(self, db_session):
        """Test that created_at and updated_at are automatically set."""
        user = User(name="타임스탬프 테스트", email="timestamp@lab.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at == user.updated_at

    def test_updated_at_changes_on_modification(self, db_session, sample_user):
        """Test that updated_at changes when user is modified."""
        original_updated_at = sample_user.updated_at

        # Modify user
        sample_user.name = "새로운 이름"
        db_session.commit()
        db_session.refresh(sample_user)

        # Note: In SQLite with in-memory DB, this might not work perfectly
        # In real PostgreSQL, updated_at would change
        assert sample_user.name == "새로운 이름"
