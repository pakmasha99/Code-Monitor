# Testing Guide - Complete Workflow

Complete end-to-end testing guide for the new features.

## Prerequisites

Ensure all services are running:

```bash
# 1. PostgreSQL (check it's running)
psql postgresql://codemonitor:codemonitor_secure_2025@localhost:5432/codemonitor -c "SELECT 1"

# 2. Qdrant (vector database)
# Check if running on port 6333

# 3. Backend FastAPI
cd backend
uvicorn app.main:app --reload

# 4. Celery Worker (for RAG indexing)
celery -A app.core.celery_app worker --loglevel=info

# 5. Frontend Next.js
cd frontend
npm run dev
```

## Test 1: Database Migration ✅

**Verify column exists:**
```sql
\d weekly_submissions;
-- Should show document_lines_added column
```

**Check data:**
```sql
SELECT id, code_lines_added, document_lines_added, documents_created
FROM weekly_submissions
LIMIT 5;
```

## Test 2: Submit Form

### Steps:
1. Navigate to http://localhost:3000/submit
2. Log in if needed
3. Check the form fields:
   - ✅ "Code Lines Added" field
   - ✅ "Document Lines Added" field (NEW)
   - ✅ Custom Repository URLs (optional)
   - ✅ Weekly Notes

### Test Cases:

**Case A: New Submission**
```
Code Lines: 450
Document Lines: 320
Notes: "Implemented auth and wrote API docs"
```
- Submit
- Check success message
- Navigate to /dashboard
- Verify "Your Lines Breakdown" shows pie chart

**Case B: Update Existing Submission**
- Visit /submit again for same week
- Should see "Update Weekly Submission"
- Values pre-filled from previous submission
- Modify document_lines_added to 500
- Submit
- Verify update successful

**Case C: Multiple Repositories**
- Add 2-3 repository URLs
- Submit
- Check backend receives custom_repo_urls array

## Test 3: Dashboard Display

### Navigate to http://localhost:3000/dashboard

**Check Stats Cards:**
- ✅ Your Rank: Shows actual rank or "N/A"
- ✅ Total Score: Sum of code + document lines
- ✅ Lines Added: Combined metric

**Check "Your Lines Breakdown" Chart:**
- ✅ Pie chart visible (if data exists)
- ✅ Blue segment: Code lines percentage
- ✅ Green segment: Document lines percentage
- ✅ Hover shows actual line counts
- ✅ Placeholder message if no data

**Check Leaderboard:**
- ✅ Shows top performers by total lines
- ✅ Scores reflect code + document lines

## Test 4: RAG Indexing

### Initialize Index:

```bash
cd backend

# Index all users
python scripts/init_rag_index.py

# Or index specific user
python scripts/init_rag_index.py --user-id 1
```

**Expected Output:**
```
🚀 Starting RAG indexing for 1 user(s)...

📍 Processing user: Your Name (ID: 1)
   Repository: https://github.com/your/repo
   ✅ Success: User 1 repository reindexing queued. Task ID: xyz-123

============================================================
✨ Indexing Summary:
   Total users: 1
   Successful: 1
   Failed: 0
============================================================
```

**Monitor Celery:**
Check celery worker terminal for progress:
- Repository cloning
- File parsing (Python, JS, etc.)
- Embedding generation
- Index building

## Test 5: Code Search & Q&A

### Navigate to http://localhost:3000/code-search

**Test Search Tab:**
1. Select search type: Hybrid (recommended)
2. Enter query: "authentication"
3. Click Search
4. **Expected**: Results with code snippets, file paths, scores
5. **Before indexing**: "No results" or error
6. **After indexing**: Relevant code chunks

**Test Q&A Tab:**
1. Enter question: "How does authentication work?"
2. Click "Ask Question"
3. **Before indexing**: Error message with reindex instructions
4. **After indexing**: Answer with source code references

## Test 6: Document Line Counting

### Test DocumentAnalyzer Service

**Create test script:**
```python
# backend/test_doc_analyzer.py
from app.services.document_analyzer import DocumentAnalyzer

analyzer = DocumentAnalyzer()

# Test PDF
pdf_lines = analyzer.count_lines_in_file("path/to/test.pdf")
print(f"PDF lines: {pdf_lines}")

# Test text file
txt_lines = analyzer.count_lines_in_file("path/to/test.txt")
print(f"Text lines: {txt_lines}")

# Test directory
results = analyzer.count_lines_in_directory("path/to/docs")
print(f"Total: {results['total_lines']}")
print(f"Breakdown: {results['breakdown']}")
```

**Run:**
```bash
cd backend
python test_doc_analyzer.py
```

## Test 7: End-to-End Workflow

### Complete User Journey:

1. **Submit Weekly Work**
   - Code: 450 lines
   - Documents: 320 lines (from PDF analysis)
   - Total: 770 lines

2. **Check Dashboard**
   - Rank updated
   - Score = 770
   - Pie chart: 58% code, 42% documents

3. **Use Code Search**
   - Search for specific code patterns
   - Get relevant results from indexed codebase

4. **Ask Questions**
   - Q: "Where is user validation?"
   - A: Detailed answer with source references

## Common Issues

### Q&A Error: "BM25 index not built"
**Solution:** Run indexing script
```bash
python scripts/init_rag_index.py --user-id YOUR_ID
```

### Dashboard Shows Zero
**Solution:** Submit weekly work first at /submit

### Form Error: "document_lines_added required"
**Solution:** Database migration not run
```bash
psql DATABASE_URL -f migrations/add_document_lines_added.sql
```

### Celery Task Stuck
**Solution:** Check Celery worker logs, ensure Qdrant running

## Success Criteria

✅ Database has document_lines_added column
✅ Submit form accepts document lines
✅ Dashboard shows breakdown pie chart
✅ RAG indexing script runs successfully
✅ Code search returns results
✅ Q&A answers questions with sources
✅ Scores reflect code + document lines

## Performance Checks

- Dashboard loads < 2 seconds
- Code search responds < 1 second
- Q&A answers < 3 seconds
- Indexing completes < 5 minutes (depends on repo size)

## Data Validation

```sql
-- Check submissions have document lines
SELECT
  u.name,
  ws.code_lines_added,
  ws.document_lines_added,
  (ws.code_lines_added + ws.document_lines_added) as total_lines
FROM weekly_submissions ws
JOIN users u ON ws.user_id = u.id
ORDER BY ws.week_start_date DESC
LIMIT 10;

-- Check rankings use combined score
SELECT
  u.name,
  r.total_score,
  r.category_scores->>'code_lines' as code,
  r.category_scores->>'document_lines' as docs
FROM rankings r
JOIN users u ON r.user_id = u.id
ORDER BY r.total_score DESC
LIMIT 10;
```

## Next Steps After Testing

1. Fix any bugs found
2. Push to production
3. Monitor user feedback
4. Optimize performance if needed
