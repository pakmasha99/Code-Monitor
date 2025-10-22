# Backend Scripts

Utility scripts for Code-Monitor backend operations.

## RAG Indexing

### `init_rag_index.py`

Initialize RAG (Retrieval-Augmented Generation) index for code search and Q&A.

**What it does:**
- Clones/pulls user repositories
- Parses code files with tree-sitter
- Generates embeddings for code chunks
- Builds BM25 + Vector indices for hybrid search

**Prerequisites:**
1. FastAPI server running (`uvicorn app.main:app`)
2. Celery worker running (`celery -A app.core.celery_app worker`)
3. PostgreSQL database running
4. Qdrant vector database running

**Usage:**

```bash
# Index all users with configured repositories
python scripts/init_rag_index.py

# Index specific user only
python scripts/init_rag_index.py --user-id 1

# Use custom API URL
python scripts/init_rag_index.py --api-url http://production-server:8000
```

**Example output:**
```
🚀 Starting RAG indexing for 3 user(s)...

📍 Processing user: Alice (ID: 1)
   Repository: https://github.com/alice/project
   ✅ Success: User 1 repository reindexing queued. Task ID: abc-123

📍 Processing user: Bob (ID: 2)
   Repository: https://github.com/bob/codebase
   ✅ Success: User 2 repository reindexing queued. Task ID: def-456

============================================================
✨ Indexing Summary:
   Total users: 2
   Successful: 2
   Failed: 0
============================================================

🎉 All indexing tasks queued successfully!
   Monitor Celery worker for progress:
   celery -A app.core.celery_app worker --loglevel=info
```

**Monitoring:**

Watch Celery worker logs to see indexing progress:
```bash
celery -A app.core.celery_app worker --loglevel=info
```

**Troubleshooting:**

- **API not responding**: Ensure FastAPI server is running on correct port
- **Celery tasks stuck**: Check Celery worker is running and configured correctly
- **Repository access denied**: Verify user repo_url is public or SSH keys configured
- **Out of memory**: Large repositories may need increased worker memory limits

**Dependencies:**
- `requests` - For API calls
- SQLAlchemy models - For database queries

---

## Ranking Recalculation

### `recalculate_rankings.py`

Recalculate all rankings in the database using the current scoring formula.

**When to use:**
- After changing the scoring formula
- When dashboard shows score mismatch (Score vs Lines Added)
- After database migrations affecting scoring logic
- To fix historical ranking data

**What it does:**
- Recalculates total_score for all rankings using current formula
- Formula: `Total Score = code_lines_added + document_lines_added`
- Updates rank_position based on new scores
- Preserves category_scores breakdown

**Prerequisites:**
1. PostgreSQL database running
2. Backend virtual environment activated

**Usage:**

```bash
# Recalculate all weeks
python scripts/recalculate_rankings.py

# Recalculate specific week only (week_start_date must be Monday)
python scripts/recalculate_rankings.py --week-start-date 2024-10-14
```

**Example output:**
```
🎯 Recalculating rankings for 1 weeks

📅 Processing week: 2025-10-20
   ✅ Success: 1 rankings updated

============================================================
✨ Recalculation Summary:
   Total weeks: 1
   Successful: 1
   Failed: 0
============================================================

🎉 All rankings recalculated successfully!
   Rankings now use formula: Total Score = code_lines_added + document_lines_added
```

**Troubleshooting:**

- **ModuleNotFoundError**: Activate virtual environment first (`source venv/bin/activate`)
- **Database connection failed**: Check PostgreSQL is running and credentials are correct
- **No submissions found**: Ensure weekly_submissions table has data
- **Updated: 0 rankings**: No users had submissions for that week

**Dependencies:**
- SQLAlchemy models - For database queries
- RankingService - For scoring logic
