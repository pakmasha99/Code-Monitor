"""
Ranking calculation and management service
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User, UserRole
from app.models.weekly_submission import WeeklySubmission
from app.models.git_metrics import GitMetrics
from app.models.ranking import Ranking


class RankingService:
    """Service for calculating and managing user rankings"""

    def calculate_weekly_score(
        self,
        user_id: int,
        week_start_date: date,
        db: Session
    ) -> Dict[str, float]:
        """
        Calculate weekly score based on total lines added.

        Score = code_lines_added + document_lines_added

        Args:
            user_id: User ID
            week_start_date: Monday of the week
            db: Database session

        Returns:
            Dict with total_score and breakdown (code_lines, document_lines)
        """
        # Get weekly submission
        submission = db.query(WeeklySubmission).filter(
            WeeklySubmission.user_id == user_id,
            WeeklySubmission.week_start_date == week_start_date
        ).first()

        # Calculate total lines
        code_lines = 0.0
        document_lines = 0.0

        if submission:
            code_lines = float(submission.code_lines_added)
            document_lines = float(submission.document_lines_added)

        total_lines = code_lines + document_lines

        return {
            'total_score': total_lines,
            'code_lines': code_lines,
            'document_lines': document_lines,
            'productivity': total_lines,  # All score is productivity
            'quality': 0.0,
            'consistency': 0.0
        }

    def update_weekly_rankings(
        self,
        week_start_date: date,
        db: Session
    ) -> Dict[str, int]:
        """
        Calculate and update rankings for all users for a specific week.

        Args:
            week_start_date: Monday of the week
            db: Database session

        Returns:
            Dict with summary statistics
        """
        # Get all active users
        users = db.query(User).filter(User.role == UserRole.STUDENT).all()

        # Calculate scores for all users
        user_scores = []
        for user in users:
            score_data = self.calculate_weekly_score(user.id, week_start_date, db)

            # Only include users with activity
            if score_data['total_score'] > 0:
                user_scores.append({
                    'user_id': user.id,
                    'score_data': score_data
                })

        # Sort by total score (descending)
        user_scores.sort(key=lambda x: x['score_data']['total_score'], reverse=True)

        # Assign ranks (handle ties)
        current_rank = 1
        previous_score = None
        updated_count = 0

        for i, user_score in enumerate(user_scores):
            score = user_score['score_data']['total_score']

            # If score is same as previous, keep same rank
            if previous_score is not None and score < previous_score:
                current_rank = i + 1

            # Check if ranking already exists
            existing_ranking = db.query(Ranking).filter(
                Ranking.user_id == user_score['user_id'],
                Ranking.week_start_date == week_start_date
            ).first()

            category_scores = {
                'productivity': user_score['score_data']['productivity'],
                'quality': user_score['score_data']['quality'],
                'consistency': user_score['score_data']['consistency']
            }

            if existing_ranking:
                # Update existing ranking
                existing_ranking.total_score = score
                existing_ranking.rank_position = current_rank
                existing_ranking.category_scores = category_scores
            else:
                # Create new ranking
                new_ranking = Ranking(
                    user_id=user_score['user_id'],
                    week_start_date=week_start_date,
                    total_score=score,
                    rank_position=current_rank,
                    category_scores=category_scores
                )
                db.add(new_ranking)

            previous_score = score
            updated_count += 1

        db.commit()

        return {
            'total_users': len(users),
            'updated': updated_count,
            'week_start_date': week_start_date.isoformat()
        }

    def get_weekly_rankings(
        self,
        week_start_date: date,
        db: Session,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get rankings for a specific week.

        Args:
            week_start_date: Monday of the week
            db: Database session
            limit: Optional limit for number of results

        Returns:
            List of ranking dicts with user information
        """
        query = db.query(Ranking).join(User).filter(
            Ranking.week_start_date == week_start_date
        ).order_by(Ranking.rank_position)

        if limit:
            query = query.limit(limit)

        rankings = query.all()

        result = []
        for ranking in rankings:
            result.append({
                'rank_position': ranking.rank_position,
                'user_id': ranking.user_id,
                'user_name': ranking.user.name,
                'user_email': ranking.user.email,
                'total_score': ranking.total_score,
                'category_scores': ranking.category_scores or {},
                'week_start_date': ranking.week_start_date.isoformat()
            })

        return result

    def get_top_performers(
        self,
        week_start_date: date,
        limit: int = 10,
        db: Session = None
    ) -> List[Dict]:
        """
        Get top N performers for a specific week.

        Args:
            week_start_date: Monday of the week
            limit: Number of top performers to return
            db: Database session

        Returns:
            List of top performer dicts
        """
        return self.get_weekly_rankings(week_start_date, db, limit=limit)

    def get_user_ranking_history(
        self,
        user_id: int,
        weeks: int,
        db: Session
    ) -> List[Dict]:
        """
        Get ranking history for a user over N weeks.

        Args:
            user_id: User ID
            weeks: Number of weeks to look back
            db: Database session

        Returns:
            List of ranking dicts ordered by week (most recent first)
        """
        # Calculate date range
        end_date = datetime.utcnow().date()
        # Get Monday of current week
        end_date = end_date - timedelta(days=end_date.weekday())
        start_date = end_date - timedelta(weeks=weeks)

        rankings = db.query(Ranking).filter(
            Ranking.user_id == user_id,
            Ranking.week_start_date >= start_date,
            Ranking.week_start_date <= end_date
        ).order_by(Ranking.week_start_date.desc()).all()

        result = []
        for ranking in rankings:
            result.append({
                'week_start_date': ranking.week_start_date.isoformat(),
                'rank_position': ranking.rank_position,
                'total_score': ranking.total_score,
                'category_scores': ranking.category_scores or {}
            })

        return result

    def get_current_week_start(self) -> date:
        """Get Monday of the current week"""
        now = datetime.utcnow()
        return (now - timedelta(days=now.weekday())).date()
