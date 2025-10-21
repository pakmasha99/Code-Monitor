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
