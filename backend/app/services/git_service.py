"""
Git repository synchronization and analysis service
"""
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import git
from git import Repo, NULL_TREE

from backend.app.core.config import get_settings

settings = get_settings()


class GitSyncService:
    """Service for syncing and analyzing git repositories"""

    def __init__(self, clone_dir: Optional[str] = None):
        self.clone_dir = Path(clone_dir or settings.GIT_CLONE_DIR)
        self.clone_dir.mkdir(parents=True, exist_ok=True)

    def get_repo_path(self, user_id: int) -> Path:
        """Get local path for user's repository"""
        return self.clone_dir / f"user_{user_id}"

    def clone_or_pull(self, repo_url: str, user_id: int) -> Repo:
        """
        Clone repository if it doesn't exist, otherwise pull latest changes.

        Args:
            repo_url: Git repository URL
            user_id: User ID for directory naming

        Returns:
            git.Repo: Repository object

        Raises:
            git.GitCommandError: If git operations fail
        """
        repo_path = self.get_repo_path(user_id)

        if repo_path.exists():
            # Repository exists - pull latest
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            origin.pull()
            print(f"✅ Pulled latest changes for user {user_id}")
        else:
            # Clone repository
            repo = Repo.clone_from(repo_url, repo_path)
            print(f"✅ Cloned repository for user {user_id}")

        return repo

    def get_commits_since(
        self,
        repo: Repo,
        since_date: datetime
    ) -> List[git.Commit]:
        """
        Get commits since a specific date.

        Args:
            repo: Git repository
            since_date: Get commits after this date

        Returns:
            List of commits
        """
        commits = []
        for commit in repo.iter_commits():
            commit_date = datetime.fromtimestamp(commit.committed_date)
            if commit_date < since_date:
                break
            commits.append(commit)

        return commits

    def analyze_commits(
        self,
        repo: Repo,
        commits: List[git.Commit]
    ) -> Dict:
        """
        Analyze commits to extract metrics.

        Returns:
            Dict with metrics:
            - commits_count: Number of commits
            - files_changed: Set of changed files
            - lines_added: Total lines added
            - lines_deleted: Total lines deleted
            - languages_breakdown: Dict of language to line count
        """
        files_changed = set()
        lines_added = 0
        lines_deleted = 0
        languages = {}

        for commit in commits:
            # Get parent commit (or empty tree for first commit)
            parent = commit.parents[0] if commit.parents else NULL_TREE

            # Analyze diffs
            diffs = commit.diff(parent)

            for diff in diffs:
                # Track changed files
                file_path = diff.a_path or diff.b_path
                if file_path:
                    files_changed.add(file_path)

                    # Detect language from extension
                    ext = Path(file_path).suffix
                    lang = self._detect_language(ext)

                    # Calculate line changes
                    if diff.diff:
                        try:
                            diff_text = diff.diff.decode('utf-8', errors='ignore')
                            lines = diff_text.split('\n')

                            added = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
                            deleted = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))

                            lines_added += added
                            lines_deleted += deleted

                            # Track by language
                            if lang:
                                languages[lang] = languages.get(lang, 0) + added

                        except Exception as e:
                            print(f"Warning: Could not analyze diff for {file_path}: {e}")

        return {
            'commits_count': len(commits),
            'files_changed': len(files_changed),
            'lines_added': lines_added,
            'lines_deleted': lines_deleted,
            'languages_breakdown': languages
        }

    def _detect_language(self, extension: str) -> Optional[str]:
        """Detect programming language from file extension"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.m': 'MATLAB',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.md': 'Markdown',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.vue': 'Vue',
        }
        return language_map.get(extension.lower())

    def cleanup_repo(self, user_id: int) -> None:
        """Delete local repository clone"""
        repo_path = self.get_repo_path(user_id)
        if repo_path.exists():
            shutil.rmtree(repo_path)
            print(f"🗑️ Cleaned up repository for user {user_id}")
