"""
RAG Indexing Tasks

Background tasks for code parsing, embedding generation, and index building.
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.code_analyzer import CodeAnalyzer
from app.services.embedding_service import EmbeddingService
from app.services.hybrid_search_service import HybridSearchService
from app.services.git_service import GitSyncService
from app.models.user import User


class RAGIndexingTask(Task):
    """Base task with shared services"""

    _code_analyzer = None
    _embedding_service = None
    _hybrid_search = None

    @property
    def code_analyzer(self):
        if self._code_analyzer is None:
            self._code_analyzer = CodeAnalyzer()
        return self._code_analyzer

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @property
    def hybrid_search(self):
        if self._hybrid_search is None:
            self._hybrid_search = HybridSearchService()
        return self._hybrid_search


@celery_app.task(base=RAGIndexingTask, bind=True, name="app.tasks.rag_indexing.reindex_repository")
def reindex_repository(self, user_id: int) -> Dict[str, Any]:
    """
    Reindex a user's repository using GitSyncService

    Steps:
    1. Fetch user and repo_url from database
    2. Clone/pull repository using GitSyncService
    3. Find all code files (Python, JavaScript, etc.)
    4. Parse with tree-sitter
    5. Generate embeddings for code chunks
    6. Build BM25 + Vector indices

    Args:
        user_id: User ID whose repository to reindex

    Returns:
        Indexing statistics
    """
    db: Session = SessionLocal()

    try:
        # 1. Get user and repository info from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.repo_url:
            return {
                "status": "error",
                "message": f"User {user_id} not found or no repository configured",
                "files_processed": 0
            }

        # 2. Clone/pull repository using GitSyncService
        git_service = GitSyncService()
        repo = git_service.clone_or_pull(user.repo_url, user.id)
        repo_path = repo.working_dir

        # 3. Find code files
        code_files = _find_code_files(repo_path)

        if not code_files:
            return {
                "status": "success",
                "message": "No code files found",
                "files_processed": 0
            }

        # 4. Parse and chunk code files
        all_chunks = []
        for file_path in code_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                chunks = self.code_analyzer.chunk_code_file(file_path, content)

                # Add metadata to chunks
                for chunk in chunks:
                    chunk['id'] = f"{file_path}:{chunk['start_line']}"
                    chunk['user_id'] = user_id
                    chunk['file_path'] = file_path  # Add file path
                    chunk['content'] = chunk['code']  # Alias for search

                all_chunks.extend(chunks)

            except Exception as e:
                # Log error but continue with other files
                print(f"Error processing {file_path}: {e}")
                continue

        # 5. Generate embeddings (async batch processing)
        embeddings_data = []
        for chunk in all_chunks:
            embedding_doc = {
                "id": chunk['id'],
                "content": chunk['content'],
                "metadata": {
                    "file_path": chunk['file_path'],
                    "language": chunk['language'],
                    "type": chunk['type'],
                    "name": chunk['name'],
                    "start_line": chunk['start_line'],
                    "end_line": chunk['end_line'],
                    "user_id": user_id
                }
            }
            embeddings_data.append(embedding_doc)

        # Store embeddings in Qdrant (batch operation)
        self.embedding_service.store_code_embeddings(embeddings_data)

        # 6. Build BM25 index
        self.hybrid_search.build_bm25_index(all_chunks)

        return {
            "status": "success",
            "user_id": user_id,
            "files_processed": len(code_files),
            "chunks_indexed": len(all_chunks),
            "message": f"Successfully indexed {len(code_files)} files for user {user_id}"
        }

    except Exception as e:
        return {
            "status": "error",
            "user_id": user_id,
            "message": f"Indexing failed: {str(e)}",
            "files_processed": 0
        }

    finally:
        db.close()


@celery_app.task(name="app.tasks.rag_indexing.reindex_all_repositories")
def reindex_all_repositories() -> Dict[str, Any]:
    """
    Reindex all active repositories

    Triggered by Celery Beat (daily schedule)
    """
    db: Session = SessionLocal()

    try:
        # TODO: Query all active repositories from database
        # For now, use placeholder
        active_repo_ids = [1, 2, 3]  # Placeholder

        results = []
        for repo_id in active_repo_ids:
            # Trigger async reindexing for each repo
            task = reindex_repository.delay(repo_id)
            results.append({
                "repository_id": repo_id,
                "task_id": task.id,
                "status": "queued"
            })

        return {
            "status": "success",
            "repositories_queued": len(results),
            "tasks": results
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to queue reindex tasks: {str(e)}"
        }

    finally:
        db.close()


@celery_app.task(base=RAGIndexingTask, bind=True, name="app.tasks.rag_indexing.analyze_code_file")
def analyze_code_file(self, file_path: str, user_id: int) -> Dict[str, Any]:
    """
    Analyze a single code file with LLM

    Used for incremental indexing when files change

    Args:
        file_path: Path to code file
        user_id: User ID

    Returns:
        Analysis results
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Analyze file with LLM
        analyzed_chunks = self.code_analyzer.analyze_file(file_path, content)

        # Store analyzed chunks
        embeddings_data = []
        for chunk in analyzed_chunks:
            embedding_doc = {
                "id": f"{file_path}:{chunk['start_line']}",
                "content": chunk['code'],
                "metadata": {
                    "file_path": file_path,
                    "language": chunk['language'],
                    "type": chunk['type'],
                    "name": chunk['name'],
                    "start_line": chunk['start_line'],
                    "end_line": chunk['end_line'],
                    "user_id": user_id,
                    "analysis": chunk.get('analysis', {})
                }
            }
            embeddings_data.append(embedding_doc)

        # Update embeddings
        self.embedding_service.store_code_embeddings(embeddings_data)

        return {
            "status": "success",
            "file_path": file_path,
            "chunks_analyzed": len(analyzed_chunks)
        }

    except Exception as e:
        return {
            "status": "error",
            "file_path": file_path,
            "message": f"Analysis failed: {str(e)}"
        }


# === Helper Functions ===

def _find_code_files(repo_path: str, extensions: List[str] = None) -> List[str]:
    """
    Find all code files in repository

    Args:
        repo_path: Repository root path
        extensions: File extensions to include (default: .py, .js, .ts)

    Returns:
        List of absolute file paths
    """
    if extensions is None:
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs']

    code_files = []
    repo_path_obj = Path(repo_path)

    for ext in extensions:
        # Recursively find files with extension
        files = repo_path_obj.rglob(f"*{ext}")

        for file_path in files:
            # Skip common ignore patterns
            path_str = str(file_path)
            if any(ignore in path_str for ignore in [
                'node_modules', '__pycache__', '.git', 'venv',
                'dist', 'build', '.pytest_cache', 'coverage'
            ]):
                continue

            code_files.append(str(file_path.absolute()))

    return code_files
