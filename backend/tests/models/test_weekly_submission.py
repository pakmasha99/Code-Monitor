"""
Tests for WeeklySubmission model.

Following TDD approach - tests define expected behavior.
"""
import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

from app.models.weekly_submission import WeeklySubmission


class TestWeeklySubmissionModel:
    """Test suite for WeeklySubmission model"""

    def test_create_submission_with_all_fields(self, db_session, sample_user):
        """Test creating a weekly submission with all fields."""
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 14),  # Monday
            code_lines_added=1245,
            code_lines_modified=340,
            documents_created=3,
            documents_modified=5,
            notes="Implemented Transformer model for text classification."
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert submission.id is not None
        assert submission.user_id == sample_user.id
        assert submission.week_start_date == date(2025, 10, 14)
        assert submission.code_lines_added == 1245
        assert submission.code_lines_modified == 340
        assert submission.documents_created == 3
        assert submission.documents_modified == 5
        assert submission.notes == "Implemented Transformer model for text classification."
        assert submission.submission_timestamp is not None

    def test_create_submission_minimal_fields(self, db_session, sample_user):
        """Test creating submission with minimal required fields."""
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 14)
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert submission.id is not None
        assert submission.code_lines_added == 0  # Default
        assert submission.code_lines_modified == 0  # Default
        assert submission.documents_created == 0  # Default
        assert submission.documents_modified == 0  # Default
        assert submission.notes is None
        assert submission.submission_timestamp is not None

    def test_user_week_combination_must_be_unique(self, db_session, sample_user):
        """Test that a user can only submit once per week."""
        week_date = date(2025, 10, 14)

        # First submission
        submission1 = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=week_date,
            code_lines_added=100
        )
        db_session.add(submission1)
        db_session.commit()

        # Duplicate submission for same user and week
        submission2 = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=week_date,
            code_lines_added=200
        )
        db_session.add(submission2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_different_users_same_week_allowed(self, db_session, sample_user, sample_advisor):
        """Test that different users can submit for the same week."""
        week_date = date(2025, 10, 14)

        submission1 = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=week_date,
            code_lines_added=100
        )
        submission2 = WeeklySubmission(
            user_id=sample_advisor.id,
            week_start_date=week_date,
            code_lines_added=200
        )

        db_session.add_all([submission1, submission2])
        db_session.commit()

        assert submission1.id is not None
        assert submission2.id is not None
        assert submission1.id != submission2.id

    def test_same_user_different_weeks_allowed(self, db_session, sample_user):
        """Test that same user can submit for different weeks."""
        submission1 = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 7),
            code_lines_added=100
        )
        submission2 = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 14),
            code_lines_added=200
        )

        db_session.add_all([submission1, submission2])
        db_session.commit()

        assert submission1.id is not None
        assert submission2.id is not None

    def test_submission_relationship_with_user(self, db_session, sample_user):
        """Test relationship between submission and user."""
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 14),
            code_lines_added=500
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        # Test relationship
        assert submission.user.id == sample_user.id
        assert submission.user.name == sample_user.name

    def test_cascade_delete_on_user_deletion(self, db_session, sample_user):
        """Test that submissions are deleted when user is deleted."""
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 14)
        )
        db_session.add(submission)
        db_session.commit()

        submission_id = submission.id

        # Delete user
        db_session.delete(sample_user)
        db_session.commit()

        # Submission should be deleted
        deleted_submission = db_session.query(WeeklySubmission).filter_by(id=submission_id).first()
        assert deleted_submission is None

    def test_submission_repr(self, db_session, sample_user):
        """Test string representation of WeeklySubmission."""
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 14)
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        repr_str = repr(submission)
        assert "WeeklySubmission" in repr_str
        assert str(submission.id) in repr_str
        assert str(submission.user_id) in repr_str

    def test_negative_values_not_enforced_by_model(self, db_session, sample_user):
        """Test that model allows negative values (business logic should validate)."""
        # Note: Negative values might represent corrections or rollbacks
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 14),
            code_lines_added=-100  # Technically allowed at DB level
        )
        db_session.add(submission)
        db_session.commit()

        assert submission.code_lines_added == -100

    def test_long_notes_field(self, db_session, sample_user):
        """Test that notes field can store long text."""
        long_notes = "A" * 5000  # 5000 characters
        submission = WeeklySubmission(
            user_id=sample_user.id,
            week_start_date=date(2025, 10, 14),
            notes=long_notes
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert len(submission.notes) == 5000
        assert submission.notes == long_notes
