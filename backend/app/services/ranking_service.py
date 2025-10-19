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

    # Score weights for different components
    WEIGHTS = {
        'commits': 2.0,
        'lines_added': 0.1,
        'files_changed': 1.5,
        'documents_created': 10.0,
        'quality_ratio': 20.0,
        'consistency_bonus': 15.0
    }

    def calculate_weekly_score(
        self,
        user_id: int,
        week_start_date: date,
        db: Session
    ) -> Dict[str, float]:
        """
        Calculate comprehensive weekly score for a user.

        Args:
            user_id: User ID
            week_start_date: Monday of the week
            db: Database session

        Returns:
            Dict with total_score and category scores (productivity, quality, consistency)
        """
        # Get git metrics
        git_metrics = db.query(GitMetrics).filter(
            GitMetrics.user_id == user_id,
            GitMetrics.week_start_date == week_start_date
        ).first()

        # Get weekly submission
        submission = db.query(WeeklySubmission).filter(
            WeeklySubmission.user_id == user_id,
            WeeklySubmission.week_start_date == week_start_date
        ).first()

        # Initialize scores
        productivity_score = 0.0
        quality_score = 0.0
        consistency_score = 0.0

        # Calculate productivity from git metrics
        if git_metrics:
            productivity_score += (
                git_metrics.commits_count * self.WEIGHTS['commits'] +
                git_metrics.lines_added * self.WEIGHTS['lines_added'] +
                git_metrics.files_changed * self.WEIGHTS['files_changed']
            )

            # Calculate quality based on code ratio
            if git_metrics.lines_added > 0:
                # Lower deletion ratio = higher quality
                deletion_ratio = git_metrics.lines_deleted / max(git_metrics.lines_added, 1)
                quality_factor = max(0, 1 - deletion_ratio)  # 0 to 1
                quality_score += quality_factor * self.WEIGHTS['quality_ratio']

            # Calculate consistency from commits
            # Ideal: 2-3 commits per day (10-15 per week)
            if git_metrics.commits_count > 0:
                # Reward consistent commits, penalty for too few or too many
                if 5 <= git_metrics.commits_count <= 20:
                    consistency_score += self.WEIGHTS['consistency_bonus']
                elif git_metrics.commits_count > 20:
                    # Slight penalty for excessive commits (might indicate poor planning)
                    consistency_score += self.WEIGHTS['consistency_bonus'] * 0.7
                else:
                    # Fewer than 5 commits
                    consistency_score += self.WEIGHTS['consistency_bonus'] * 0.4

        # Add manual submission data
        if submission:
            productivity_score += (
                submission.code_lines_added * self.WEIGHTS['lines_added'] +
                submission.documents_created * self.WEIGHTS['documents_created']
            )

        # Calculate total score
        total_score = productivity_score + quality_score + consistency_score

        return {
            'total_score': round(total_score, 2),
            'productivity': round(productivity_score, 2),
            'quality': round(quality_score, 2),
            'consistency': round(consistency_score, 2)
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
