# RAG System Implementation Plan
**Date**: 2025-10-21
**Status**: Ready to implement - Repository access confirmed ✅

## Executive Summary

Based on investigation of the current Code-Monitor system and review of the original `lab-knowledge-system-design.md`, **the RAG system can be implemented**. Key findings:

### ✅ CONFIRMED: Repository Access Working
- Server has SSH keys configured and can clone/read GitHub repositories
- Successfully tested with `git@github.com:jcha9928/Code-Monitor.git`
- 15 users registered with GitHub repository URLs (mix of HTTPS and SSH)
- Multiple repository URL support just implemented (up to 5 repos per submission)

### 🟢 INFRASTRUCTURE READY
- PostgreSQL database operational
- FastAPI backend with async support
- Celery + Redis packages installed (Celery 5.3.6, Redis 5.0.1)
- Git integration working (GitPython)
- Next.js frontend for UI components

### ⚠️ MISSING COMPONENTS
- Redis server not running (or not installed)
- Qdrant vector database not installed
- LLM integration (OpenAI/Claude API) not configured
- Code analysis pipeline not implemented
- Database schema extensions needed
- RAG query UI components

---

## Current State Assessment

### Phase 1: MVP (COMPLETE ✅)
From `lab-knowledge-system-design.md` - All basic monitoring features working:
- User management system
- Manual weekly submission forms
- Git metrics collection
- Simple leaderboard and rankings
- Individual profile pages with charts
- Admin dashboard

### Repository Access Details

**Registered Users** (15 total):
```
1. Jiook Cha → git@github.com:jcha9928/Code-Monitor.git (SSH)
2-15. Other lab members → HTTPS profile URLs
```

**Known Issues**:
- Most users have profile URLs (e.g., `https://github.com/username`) not specific repo URLs
- Need to collect actual repository URLs for each user
- Many may be **private** lab repositories requiring authentication

**Access Verification**:
- ✅ Server CAN clone via SSH (`git@github.com:...`)
- ✅ GitPython installed and working
- ✅ Multiple repo URLs now supported per submission
- ❓ Need to verify private repository access for lab members

---

## Implementation Phases

### Phase 2: Infrastructure Setup (Weeks 1-2)

#### 2.1 Redis Server Installation
```bash
# On connectome server
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify
redis-cli ping  # Should return "PONG"
```

#### 2.2 Qdrant Vector Database Setup
```bash
# Install Qdrant (Docker recommended)
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# Or install Python client
pip install qdrant-client
```

#### 2.3 Database Schema Extensions
**New tables needed** (`backend/app/models/code_analysis.py`):

```python
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class CodeAnalysis(Base):
    __tablename__ = "code_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repository_url = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    commit_hash = Column(String(40), index=True)

    # Code structure
    function_name = Column(String(200))
    class_name = Column(String(200))
    code_snippet = Column(Text)  # Store code chunk

    # LLM analysis results
    analysis_summary = Column(Text)  # Short summary
    complexity_score = Column(Float)  # 1-10 scale
    quality_metrics = Column(JSON)  # Flexible JSON field

    # Metadata
    language = Column(String(50))  # Python, JavaScript, etc.
    lines_of_code = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="code_analyses")

# Update User model
# In app/models/user.py add:
# code_analyses = relationship("CodeAnalysis", back_populates="user")
```

**Migration**:
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Add code_analysis table for RAG"
alembic upgrade head
```

#### 2.4 Python Dependencies
Add to `backend/requirements.txt`:
```
# LLM Integration
anthropic>=0.8.0
openai>=1.0.0

# Vector Database
qdrant-client>=1.7.0

# Code Analysis
tree-sitter>=0.20.0
tree-sitter-python>=0.20.0
tree-sitter-javascript>=0.20.0

# Already installed (verify versions)
celery>=5.3.0
redis>=5.0.0
```

Install:
```bash
cd backend
source venv/bin/activate
pip install anthropic openai qdrant-client tree-sitter tree-sitter-python tree-sitter-javascript
pip freeze > requirements.txt
```

---

### Phase 3: LLM Integration (Weeks 3-4)

#### 3.1 API Configuration
Add to `backend/.env`:
```bash
# LLM API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0
```

#### 3.2 Code Analysis Service
Create `backend/app/services/code_analyzer.py`:

```python
from anthropic import Anthropic
import openai
from tree_sitter import Language, Parser
import os

class CodeAnalyzer:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.setup_parsers()

    def setup_parsers(self):
        """Setup tree-sitter parsers for different languages"""
        # Load language grammars
        self.parsers = {
            'python': self.create_parser('python'),
            'javascript': self.create_parser('javascript'),
            'typescript': self.create_parser('typescript'),
        }

    def create_parser(self, language: str) -> Parser:
        """Create parser for specific language"""
        parser = Parser()
        # Language.build_library(...) would be called during setup
        # For now, simplified
        return parser

    def chunk_code_file(self, file_path: str, content: str) -> list:
        """Parse code into logical chunks using tree-sitter"""
        language = self.detect_language(file_path)
        parser = self.parsers.get(language)

        if not parser:
            # Fallback: split by functions/classes using simple heuristics
            return self.simple_chunk(content)

        tree = parser.parse(bytes(content, 'utf8'))
        chunks = []

        for node in tree.root_node.children:
            if node.type in ['function_definition', 'class_definition',
                            'function_declaration', 'class_declaration']:
                chunk = {
                    'type': node.type,
                    'name': self.extract_name(node),
                    'code': content[node.start_byte:node.end_byte],
                    'start_line': node.start_point[0],
                    'end_line': node.end_point[0],
                    'language': language
                }
                chunks.append(chunk)

        return chunks

    async def analyze_code_chunk(self, chunk: dict) -> dict:
        """Analyze code chunk with Claude 3.5 Sonnet"""
        prompt = f"""Analyze this {chunk['language']} {chunk['type']} code:

```{chunk['language']}
{chunk['code']}
```

Provide a JSON response with:
1. "summary": One-sentence description of what this code does
2. "purpose": Detailed explanation of its purpose
3. "complexity": Complexity score from 1-10 (1=trivial, 10=very complex)
4. "algorithms": List of key algorithms or patterns used
5. "quality": Code quality assessment (readability, maintainability, best practices)

Format as valid JSON only, no markdown.
"""

        message = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        import json
        analysis = json.loads(message.content[0].text)
        return analysis

    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = file_path.split('.')[-1].lower()
        mapping = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'javascript',
            'tsx': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rs': 'rust'
        }
        return mapping.get(ext, 'unknown')

    def extract_name(self, node) -> str:
        """Extract function/class name from AST node"""
        # Simplified - actual implementation would traverse to name node
        return "extracted_name"

    def simple_chunk(self, content: str) -> list:
        """Fallback simple chunking for unsupported languages"""
        # Split by function definitions, class definitions, etc.
        lines = content.split('\n')
        chunks = []
        current_chunk = []

        for i, line in enumerate(lines):
            if line.strip().startswith(('def ', 'class ', 'function ', 'async def ')):
                if current_chunk:
                    chunks.append({
                        'code': '\n'.join(current_chunk),
                        'type': 'unknown',
                        'language': 'unknown'
                    })
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk:
            chunks.append({
                'code': '\n'.join(current_chunk),
                'type': 'unknown',
                'language': 'unknown'
            })

        return chunks
```

#### 3.3 Embedding Generation
Create `backend/app/services/embedding_service.py`:

```python
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os

class EmbeddingService:
    def __init__(self):
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        self.collection_name = "code_embeddings"
        self.ensure_collection()

    def ensure_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        collections = self.client.get_collections()
        if self.collection_name not in [c.name for c in collections.collections]:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI text-embedding-3-small dimension
                    distance=Distance.COSINE
                )
            )

    async def generate_embedding(self, text: str) -> list:
        """Generate embedding using OpenAI text-embedding-3-small"""
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def store_code_embedding(self, code_analysis: dict, chunk: dict, user_info: dict):
        """Store code embedding in Qdrant"""
        # Prepare text for embedding
        text_to_embed = f"""
        Function: {chunk.get('name', 'unknown')}
        Summary: {code_analysis['summary']}
        Code: {chunk['code'][:500]}  # Limit code snippet length
        """

        # Generate embedding
        embedding = await self.generate_embedding(text_to_embed)

        # Prepare metadata
        point = PointStruct(
            id=hash(f"{user_info['user_id']}_{chunk['name']}_{chunk['start_line']}"),
            vector=embedding,
            payload={
                "user_id": user_info['user_id'],
                "user_name": user_info['user_name'],
                "repository_url": user_info['repository_url'],
                "file_path": chunk.get('file_path', ''),
                "function_name": chunk.get('name', ''),
                "class_name": chunk.get('class_name', ''),
                "code_snippet": chunk['code'][:500],
                "summary": code_analysis['summary'],
                "language": chunk['language'],
                "complexity_score": code_analysis['complexity'],
                "timestamp": user_info.get('timestamp', ''),
                "commit_hash": user_info.get('commit_hash', '')
            }
        )

        # Store in Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    async def search_similar_code(self, query: str, limit: int = 20, filters: dict = None):
        """Search for similar code using vector similarity"""
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Prepare filters
        qdrant_filter = None
        if filters:
            # Convert filters to Qdrant filter format
            # Example: filters = {"language": "python", "user_id": 5}
            pass

        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=qdrant_filter
        )

        return results
```

---

### Phase 4: Background Task Processing (Weeks 5-6)

#### 4.1 Celery Configuration
Create `backend/app/celery_app.py`:

```python
from celery import Celery
import os

celery_app = Celery(
    'code_monitor',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])
```

#### 4.2 Repository Sync Tasks
Create `backend/app/tasks/repo_sync.py`:

```python
from celery import shared_task
from app.services.code_analyzer import CodeAnalyzer
from app.services.embedding_service import EmbeddingService
from app.models.user import User
from app.models.code_analysis import CodeAnalysis
from app.core.database import SessionLocal
import git
import os
from pathlib import Path

@shared_task
def sync_user_repositories(user_id: int):
    """Sync all repositories for a user and analyze code"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.repo_url:
            return {"status": "error", "message": "User or repo_url not found"}

        # Get all repository URLs for this user
        # Check both default repo_url and any custom_repo_urls from recent submissions
        repo_urls = [user.repo_url]  # Start with default

        # Clone/pull each repository
        for repo_url in repo_urls:
            analyze_repository.delay(user_id, repo_url)

        return {"status": "success", "repositories": len(repo_urls)}
    finally:
        db.close()

@shared_task
def analyze_repository(user_id: int, repo_url: str):
    """Clone repository and analyze all code files"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        # Clone repository
        repo_path = f"/tmp/code-monitor/repos/{user_id}/{repo_url.split('/')[-1].replace('.git', '')}"
        os.makedirs(os.path.dirname(repo_path), exist_ok=True)

        if os.path.exists(repo_path):
            # Pull latest
            repo = git.Repo(repo_path)
            repo.remotes.origin.pull()
        else:
            # Clone fresh
            repo = git.Repo.clone_from(repo_url, repo_path)

        # Get current commit hash
        commit_hash = repo.head.commit.hexsha

        # Find all code files
        code_files = []
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.go', '.rs']:
            code_files.extend(Path(repo_path).rglob(f'*{ext}'))

        # Analyze each file
        for file_path in code_files:
            analyze_code_file.delay(
                user_id=user_id,
                repo_url=repo_url,
                file_path=str(file_path),
                commit_hash=commit_hash
            )

        return {"status": "success", "files": len(code_files)}

    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

@shared_task
async def analyze_code_file(user_id: int, repo_url: str, file_path: str, commit_hash: str):
    """Analyze a single code file and store embeddings"""
    db = SessionLocal()
    analyzer = CodeAnalyzer()
    embedding_service = EmbeddingService()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Chunk code into functions/classes
        chunks = analyzer.chunk_code_file(file_path, content)

        for chunk in chunks:
            # Analyze with LLM
            analysis = await analyzer.analyze_code_chunk(chunk)

            # Store in database
            code_analysis = CodeAnalysis(
                user_id=user_id,
                repository_url=repo_url,
                file_path=file_path,
                commit_hash=commit_hash,
                function_name=chunk.get('name'),
                code_snippet=chunk['code'][:1000],
                analysis_summary=analysis['summary'],
                complexity_score=analysis['complexity'],
                quality_metrics=analysis,
                language=chunk['language'],
                lines_of_code=len(chunk['code'].split('\n'))
            )
            db.add(code_analysis)
            db.commit()

            # Generate and store embedding
            await embedding_service.store_code_embedding(
                code_analysis=analysis,
                chunk=chunk,
                user_info={
                    'user_id': user_id,
                    'user_name': user.name,
                    'repository_url': repo_url,
                    'commit_hash': commit_hash,
                    'timestamp': code_analysis.created_at.isoformat()
                }
            )

        return {"status": "success", "chunks": len(chunks)}

    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
```

#### 4.3 Start Celery Worker
```bash
# On connectome server
cd ~/code-monitor/backend
source venv/bin/activate

# Start Celery worker
celery -A app.celery_app worker --loglevel=info

# For production, use supervisor or systemd
```

---

### Phase 5: RAG Query System (Weeks 7-8)

#### 5.1 RAG Query Handler
Create `backend/app/services/rag_query_handler.py`:

```python
from app.services.embedding_service import EmbeddingService
from anthropic import Anthropic
import os

class RAGQueryHandler:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def query(self, user_question: str, filters: dict = None) -> dict:
        """
        Main RAG query pipeline
        1. Query understanding
        2. Vector search
        3. Reranking
        4. LLM response generation
        """
        # 1. Vector search for similar code
        search_results = await self.embedding_service.search_similar_code(
            query=user_question,
            limit=20,
            filters=filters
        )

        # 2. Rerank results
        top_results = self.rerank(search_results, user_question)

        # 3. Generate response with Claude
        response = await self.generate_response(user_question, top_results)

        return {
            "answer": response,
            "sources": top_results,
            "query": user_question
        }

    def rerank(self, results: list, query: str) -> list:
        """
        Rerank results based on:
        - Semantic relevance (from vector search score)
        - Code quality (complexity, best practices)
        - Recency (newer code preferred)
        - Diversity (different approaches)
        """
        scored_results = []

        for result in results:
            payload = result.payload
            score = (
                result.score * 0.6 +  # Semantic relevance
                (payload.get('complexity_score', 5) / 10) * 0.2 +  # Quality
                self.recency_score(payload.get('timestamp', '')) * 0.1 +  # Recency
                self.diversity_score(payload, scored_results) * 0.1  # Diversity
            )
            scored_results.append((score, result))

        # Sort by score
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Return top 5
        return [result for score, result in scored_results[:5]]

    def recency_score(self, timestamp: str) -> float:
        """Calculate recency score (0-1)"""
        from datetime import datetime
        if not timestamp:
            return 0.5

        try:
            dt = datetime.fromisoformat(timestamp)
            age_days = (datetime.now() - dt).days
            # Exponential decay: score = e^(-age_days/30)
            import math
            return math.exp(-age_days / 30)
        except:
            return 0.5

    def diversity_score(self, payload: dict, existing: list) -> float:
        """Encourage diversity in results"""
        # Check if this user/repo is already represented
        user_id = payload.get('user_id')
        existing_users = [r[1].payload.get('user_id') for r in existing]

        if user_id in existing_users:
            return 0.0
        return 1.0

    async def generate_response(self, question: str, code_results: list) -> str:
        """Generate final response using Claude with RAG context"""

        # Prepare context from code results
        context = "\n\n".join([
            f"## Example {i+1} (by {result.payload['user_name']})\n"
            f"**File**: {result.payload['file_path']}\n"
            f"**Function**: {result.payload.get('function_name', 'N/A')}\n"
            f"**Summary**: {result.payload['summary']}\n"
            f"```{result.payload['language']}\n{result.payload['code_snippet']}\n```"
            for i, result in enumerate(code_results)
        ])

        prompt = f"""You are a helpful coding assistant for a research lab.
A lab member asked: "{question}"

I've found relevant code examples from other lab members:

{context}

Based on these examples, provide a comprehensive answer that:
1. Summarizes the different approaches found
2. Compares their trade-offs
3. Recommends which approach to use based on the context
4. Provides code examples if helpful

Be concise but thorough. If the code examples don't fully answer the question, acknowledge that.
"""

        message = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return message.content[0].text
```

#### 5.2 RAG API Endpoints
Create `backend/app/api/rag.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.services.rag_query_handler import RAGQueryHandler
from app.tasks.repo_sync import sync_user_repositories

router = APIRouter(prefix="/api/rag", tags=["RAG"])

class RAGQuery(BaseModel):
    question: str
    language: str = None  # Optional filter
    user_id: int = None  # Optional filter

class RAGResponse(BaseModel):
    answer: str
    sources: list
    query: str

@router.post("/query", response_model=RAGResponse)
async def rag_query(query: RAGQuery):
    """
    Query the RAG system to find code examples from lab members

    Example:
    {
        "question": "다른 사람들이 인증 어떻게 구현했는지 알려줘",
        "language": "python"
    }
    """
    handler = RAGQueryHandler()

    filters = {}
    if query.language:
        filters['language'] = query.language
    if query.user_id:
        filters['user_id'] = query.user_id

    result = await handler.query(query.question, filters)
    return result

@router.post("/sync/{user_id}")
async def sync_user_code(user_id: int):
    """
    Trigger background sync of user's repositories
    This will clone/pull repos and analyze code
    """
    task = sync_user_repositories.delay(user_id)
    return {
        "task_id": task.id,
        "status": "processing",
        "message": f"Started syncing repositories for user {user_id}"
    }
```

Add to `backend/app/main.py`:
```python
from app.api import rag

app.include_router(rag.router)
```

---

### Phase 6: Frontend UI (Weeks 9-10)

#### 6.1 RAG Query Page
Create `frontend/src/app/rag/page.tsx`:

```typescript
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import RAGClient from "./RAGClient";

export default async function RAGPage() {
  const session = await auth();

  if (!session?.user) {
    redirect('/');
  }

  return <RAGClient userEmail={session.user.email!} />;
}
```

Create `frontend/src/app/rag/RAGClient.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { Button } from "@/components/ui/button";

interface RAGSource {
  user_name: string;
  file_path: string;
  function_name: string;
  summary: string;
  code_snippet: string;
  language: string;
}

interface RAGResponse {
  answer: string;
  sources: RAGSource[];
  query: string;
}

export default function RAGClient({ userEmail }: { userEmail: string }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<RAGResponse | null>(null);

  async function handleQuery(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query })
      });

      const data = await res.json();
      setResponse(data);
    } catch (error) {
      console.error('RAG query failed:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">🤖 Code Knowledge Search</h1>

      <form onSubmit={handleQuery} className="mb-8">
        <div className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 다른 사람들이 인증 어떻게 구현했는지 알려줘"
            className="flex-1 px-4 py-2 rounded-md border"
          />
          <Button type="submit" disabled={loading || !query}>
            {loading ? '🔍 Searching...' : '🔍 Search'}
          </Button>
        </div>
      </form>

      {response && (
        <div className="space-y-6">
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-bold mb-4">💡 Answer</h2>
            <div className="prose max-w-none">
              {response.answer}
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold">📚 Code Examples</h2>
            {response.sources.map((source, idx) => (
              <div key={idx} className="rounded-lg border bg-card p-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold">{source.user_name}</span>
                  <span className="text-sm text-muted-foreground">
                    {source.file_path}
                  </span>
                </div>
                <p className="text-sm mb-3">{source.summary}</p>
                <pre className="bg-muted p-4 rounded-md overflow-x-auto">
                  <code className={`language-${source.language}`}>
                    {source.code_snippet}
                  </code>
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

Add link to dashboard navigation (`frontend/src/app/dashboard/page.tsx`):
```typescript
<Link href="/rag">
  <Button variant="outline">
    🤖 Code Search
  </Button>
</Link>
```

---

## Quick Start Guide (MVP RAG)

For fastest implementation, start with this simplified version:

### Week 1: Manual Testing
1. Install Redis: `sudo apt install redis-server`
2. Install Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
3. Install Python packages: `pip install anthropic qdrant-client`
4. Create simple script to:
   - Clone a test repository
   - Extract one Python file
   - Send to Claude for analysis
   - Store embedding in Qdrant
   - Query it back

### Week 2: Basic API
1. Add RAG query endpoint
2. Simple frontend page
3. Test with real lab member code

### Week 3-4: Background Processing
1. Set up Celery
2. Automate repository syncing
3. Scale to all lab members

---

## Repository Access Requirements

### Critical Next Steps

1. **Collect Repository URLs**
   - Most users have profile URLs, not repo URLs
   - Need to ask each lab member for their actual repository URL(s)
   - Determine which repos are private vs public

2. **Configure Authentication**
   - For private repositories, need:
     - GitHub Personal Access Token (PAT) with repo read permissions
     - OR: Add connectome server SSH key to each private repo
   - Store credentials securely (environment variables or secret manager)

3. **Test Access**
   ```bash
   # Test public repo
   git clone https://github.com/user/repo

   # Test private repo with PAT
   git clone https://oauth2:YOUR_PAT@github.com/user/private-repo

   # Test private repo with SSH
   git clone git@github.com:user/private-repo
   ```

---

## Estimated Timeline

| Phase | Duration | Effort | Status |
|-------|----------|--------|--------|
| Infrastructure Setup | 1-2 weeks | Medium | ⏸️ Pending Redis/Qdrant install |
| LLM Integration | 2-3 weeks | High | ⏸️ Pending API keys |
| Background Tasks | 2 weeks | Medium | 🟡 Celery installed, needs config |
| RAG Query System | 2-3 weeks | High | ⏸️ Pending Qdrant + LLM |
| Frontend UI | 1-2 weeks | Medium | ⏸️ Pending backend |
| Testing & Polish | 1-2 weeks | Medium | ⏸️ Pending implementation |
| **Total** | **9-14 weeks** | **High** | **~3.5 months** |

---

## Cost Estimates

### OpenAI API (Embeddings)
- Model: text-embedding-3-small
- Cost: $0.02 per 1M tokens
- Estimate: 15 users × 10 repos × 100 files × 2KB/file = ~30M chars = ~7.5M tokens
- **Cost**: ~$0.15 for initial indexing + ~$0.01/week for updates
- **Annual**: ~$1

### Claude API (Code Analysis)
- Model: claude-3-5-sonnet-20241022
- Cost: $3 per 1M input tokens, $15 per 1M output tokens
- Estimate: Same 15,000 code chunks × 500 tokens input × 200 tokens output
- Input: 7.5M tokens = $22.50
- Output: 3M tokens = $45
- **Initial**: ~$67.50 for full codebase
- **Ongoing**: ~$5/week for new code
- **Annual**: ~$327

### Qdrant (Vector Database)
- Self-hosted: FREE (using Docker)
- Cloud: $75/month for 1M vectors
- **Recommendation**: Self-host initially

### Total Annual Cost
- **Initial setup**: ~$70
- **Ongoing annual**: ~$330
- **Monthly**: ~$27

---

## Next Actions (Priority Order)

1. **Immediate** (This week):
   - [ ] Install Redis server on connectome
   - [ ] Set up Qdrant (Docker)
   - [ ] Get Anthropic API key
   - [ ] Get OpenAI API key
   - [ ] Test basic embedding generation

2. **Week 1-2**:
   - [ ] Collect actual repository URLs from lab members
   - [ ] Test repository access (public vs private)
   - [ ] Create `code_analysis` table migration
   - [ ] Implement basic `CodeAnalyzer` class
   - [ ] Test with one repository manually

3. **Week 3-4**:
   - [ ] Implement Celery tasks
   - [ ] Set up automatic repository syncing
   - [ ] Build RAG query handler
   - [ ] Create API endpoints

4. **Week 5-6**:
   - [ ] Build frontend UI
   - [ ] Integration testing
   - [ ] Performance optimization
   - [ ] Deploy to production

---

## Risks & Mitigations

### Risk 1: Private Repository Access
- **Risk**: Most lab repositories may be private
- **Mitigation**: Set up GitHub PAT or SSH keys for server
- **Fallback**: Start with public repos only for MVP

### Risk 2: LLM API Costs
- **Risk**: Costs could escalate with many code files
- **Mitigation**:
  - Cache analyses (don't re-analyze unchanged files)
  - Rate limiting
  - Budget alerts
  - Start with smaller batch for testing

### Risk 3: Vector DB Performance
- **Risk**: Slow search with many embeddings
- **Mitigation**:
  - Qdrant is designed for this (handles millions of vectors)
  - Index optimization
  - Consider filters to reduce search space

### Risk 4: Code Quality Variability
- **Risk**: Some code may be poorly written/documented
- **Mitigation**:
  - LLM can still analyze and summarize
  - Add quality scores to help users filter
  - Human feedback loop for refinement

---

## Success Metrics

After implementation, measure:
- **Adoption**: % of lab members using RAG search weekly
- **Query satisfaction**: User feedback on answer quality
- **Coverage**: % of codebase analyzed and embedded
- **Performance**: Average query response time (<3 seconds target)
- **Cost**: Actual API spending vs budget

---

## Conclusion

✅ **READY TO IMPLEMENT**

The RAG system implementation is feasible with current infrastructure. Key findings:
- Repository access works (SSH verified)
- Celery + Redis already installed
- Clear architecture from original design doc
- Estimated 3-4 months for full implementation
- Reasonable costs (~$330/year)

**Recommended start**: MVP in 4 weeks focusing on manual repository sync and basic RAG query before automating with Celery.
