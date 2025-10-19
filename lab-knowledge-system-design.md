# 연구실 지식 증류 시스템 설계 문서
## Lab Knowledge Distillation & Productivity Monitoring System

**설계 날짜:** 2025-10-19
**대상:** 20명 규모 연구실
**목적:** 코드/문서 생성량 모니터링, 실시간 랭킹, LLM 기반 지식 공유

---

## 📋 Executive Summary

본 시스템은 연구실 구성원들의 주간 생산성을 자동/수동으로 추적하고, LLM 기반 RAG(Retrieval-Augmented Generation)를 통해 팀 전체의 코드 지식을 공유 가능한 지식 베이스로 전환합니다. 실시간 대시보드를 통해 최고 수행자를 랭킹하고, 구성원 간 학습을 촉진하는 지식 증류(Knowledge Distillation) 플랫폼입니다.

**핵심 기능:**
- ✅ 주간 코드/문서 생성량 자동 수집 (Git 분석)
- ✅ 수동 제출 인터페이스 (자체 평가 + 노트)
- ✅ 실시간 랭킹 대시보드
- ✅ 종단적 데이터 분석 (시계열 트렌드)
- ✅ LLM 기반 코드 분석 및 문서화
- ✅ Vector DB 기반 의미적 코드 검색
- ✅ RAG 시스템으로 "다른 사람 코드 어떻게 작성했는지" 질의응답

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Dashboard                        │
│  (Streamlit/React - Real-time Leaderboard, Analytics, RAG UI)  │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API + WebSocket
┌────────────────────────┴────────────────────────────────────────┐
│                     Backend API Layer (FastAPI)                  │
│  - Authentication  - Metrics API  - RAG Query API               │
└─────┬──────────────────┬───────────────────┬────────────────────┘
      │                  │                   │
      ▼                  ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
│  PostgreSQL  │  │   Qdrant     │  │  Background     │
│   Database   │  │  Vector DB   │  │  Workers        │
│              │  │              │  │  (Celery+Redis) │
│ - Users      │  │ - Code       │  │                 │
│ - Metrics    │  │   Embeddings │  │ - Git Sync      │
│ - Rankings   │  │ - Metadata   │  │ - LLM Analysis  │
│ - Analysis   │  │              │  │ - Embedding Gen │
└──────────────┘  └──────────────┘  └─────────────────┘
      ▲                  ▲                   ▲
      │                  │                   │
      └──────────────────┴───────────────────┘
                         │
      ┌──────────────────┴───────────────────────┐
      │  Data Collection & Processing Pipeline   │
      │  - GitPython (repo monitoring)           │
      │  - LLM Code Analyzer (GPT-4/Claude)      │
      │  - Embedding Generator (OpenAI/Local)    │
      └──────────────────────────────────────────┘
                         ▲
      ┌──────────────────┴───────────────────────┐
      │  Member Git Repositories (Shared Access) │
      │  - 20 individual repos                   │
      │  - Internal network access               │
      └──────────────────────────────────────────┘
```

---

## 🗂️ Component Breakdown

### 1. Data Collection Layer

**1.1 Manual Submission Interface**
- 주간 제출 양식 (Web Form)
  - 코드 라인 수 (추가/수정)
  - 문서 개수 (생성/수정)
  - 자유 노트 (주간 작업 요약)
- 제출 시 자동으로 Git 메트릭과 비교 검증

**1.2 Automated Git Monitoring**
- GitPython을 통한 레포지토리 동기화
- 일일/주간 스케줄링된 분석
- 수집 데이터:
  - Commit 수, 변경된 파일
  - Lines of Code (추가/삭제)
  - 사용 언어 분포
  - 커밋 메시지 분석

**1.3 Webhook Integration (Optional)**
- GitHub/GitLab webhook으로 실시간 업데이트
- Push 이벤트 시 즉시 분석 트리거

---

### 2. Processing Layer

**2.1 Git Analyzer**
- 기능:
  - Diff 분석으로 코드 변경량 추출
  - 파일 타입별 분류 (Python, JS, etc.)
  - 작성자별 기여도 계산
- 도구: GitPython, tree-sitter (AST parsing)

**2.2 LLM Code Analysis Agent**
- 역할:
  - 코드 청크 단위로 요약 생성
  - 함수/클래스 목적 파악
  - 복잡도 및 품질 평가
  - 알고리즘/패턴 식별
- 모델: GPT-4, Claude 3.5, 또는 CodeLlama (로컬)
- 출력: 각 코드 단위별 요약 및 메타데이터

**2.3 Embedding Generator**
- 코드 → 벡터 변환
- 모델 선택:
  - OpenAI text-embedding-3-small (추천)
  - 로컬: sentence-transformers/all-MiniLM-L6-v2
- 전략:
  - 원본 코드 + LLM 요약 결합 임베딩
  - 함수/클래스 단위로 분할
  - 메타데이터와 함께 저장

**2.4 Metrics Calculator**
- 주간 집계:
  - 개인별 코드 생산량
  - 문서 기여도
  - 품질 점수 (LLM 평가 기반)
  - 지식 공유 점수 (RAG 쿼리 횟수)
- 랭킹 알고리즘 적용

---

### 3. Storage Layer

**3.1 PostgreSQL Database**

**Schema:**

```sql
-- 사용자 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    github_username VARCHAR(100),
    repo_url TEXT,
    joined_date DATE DEFAULT CURRENT_DATE,
    role VARCHAR(20) DEFAULT 'student'
);

-- 주간 제출 기록
CREATE TABLE weekly_submissions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    week_start_date DATE NOT NULL,
    code_lines_added INT DEFAULT 0,
    code_lines_modified INT DEFAULT 0,
    documents_created INT DEFAULT 0,
    documents_modified INT DEFAULT 0,
    notes TEXT,
    submission_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, week_start_date)
);

-- Git 자동 수집 메트릭
CREATE TABLE git_metrics (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    repo_url TEXT,
    week_start_date DATE NOT NULL,
    commits_count INT DEFAULT 0,
    files_changed INT DEFAULT 0,
    lines_added INT DEFAULT 0,
    lines_deleted INT DEFAULT 0,
    languages_breakdown JSONB,  -- {"Python": 1200, "JavaScript": 340}
    last_sync_timestamp TIMESTAMP,
    UNIQUE(user_id, week_start_date)
);

-- 랭킹 테이블
CREATE TABLE rankings (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    week_start_date DATE NOT NULL,
    total_score FLOAT DEFAULT 0,
    rank_position INT,
    category_scores JSONB,  -- {"code": 80, "docs": 60, "quality": 75, "sharing": 40}
    UNIQUE(user_id, week_start_date)
);

-- 코드 분석 결과
CREATE TABLE code_analysis (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    file_path TEXT NOT NULL,
    commit_hash VARCHAR(40),
    function_name VARCHAR(200),
    class_name VARCHAR(200),
    analysis_summary TEXT,  -- LLM 생성 요약
    complexity_score FLOAT,
    quality_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_weekly_submissions_user_date ON weekly_submissions(user_id, week_start_date);
CREATE INDEX idx_git_metrics_user_date ON git_metrics(user_id, week_start_date);
CREATE INDEX idx_rankings_week ON rankings(week_start_date DESC, rank_position);
CREATE INDEX idx_code_analysis_user ON code_analysis(user_id, created_at DESC);
```

**3.2 Qdrant Vector Database**

**Collection: code_embeddings**

```python
{
    "vector": [0.123, -0.456, ...],  # 임베딩 벡터 (1536 dim)
    "payload": {
        "user_id": 5,
        "user_name": "김철수",
        "file_path": "src/models/transformer.py",
        "function_name": "multi_head_attention",
        "class_name": "TransformerEncoder",
        "code_snippet": "def multi_head_attention(query, key, value, mask=None):\n    ...",
        "summary": "멀티헤드 어텐션 메커니즘 구현. Query, Key, Value 텐서를 받아 어텐션 가중치 계산",
        "language": "Python",
        "timestamp": "2025-10-15T10:30:00Z",
        "commit_hash": "a3f5b2c",
        "complexity_score": 6.5,
        "lines_of_code": 45
    }
}
```

**설정:**
- Distance metric: Cosine similarity
- Vector dimension: 1536 (OpenAI embedding)
- HNSW index for fast approximate search

---

### 4. RAG/Query Layer

**4.1 Query Processing Pipeline**

```
User Query: "다른 사람들이 인증 어떻게 구현했는지 알려줘"
    ↓
1. Query Understanding (LLM)
   - Intent: 예제 코드 검색
   - Entities: authentication, implementation patterns
    ↓
2. Hybrid Retrieval
   a) Vector Search (Qdrant)
      - Query embedding
      - Top-20 semantic matches
   b) Metadata Filtering
      - Language: Python (auto-detected)
      - Recency: last 3 months
    ↓
3. Reranking
   - Relevance score (vector similarity)
   - Quality score (code metrics)
   - Diversity (different authors)
   → Top-5 results
    ↓
4. Context Assembly
   - Retrieve code snippets + summaries
   - Author info + performance notes
    ↓
5. LLM Response Generation
   Prompt: """
   User asked: {query}

   Here are relevant code examples from teammates:

   [Example 1 - 김철수]
   {code_snippet_1}
   Summary: {summary_1}

   [Example 2 - 이영희]
   {code_snippet_2}
   Summary: {summary_2}

   Synthesize these approaches and recommend best practices.
   """
    ↓
6. Formatted Response
   - Comparison table
   - Code examples with syntax highlighting
   - Links to full files
   - Recommendations
```

**4.2 Knowledge Distillation Features**

- **Cross-member Pattern Detection:**
  - "누가 가장 효율적인 정렬 알고리즘 사용했나?"
  - "같은 문제를 해결한 다른 접근법들은?"

- **Performance Queries:**
  - "이 코드의 시간 복잡도는?"
  - "메모리 효율적인 구현 예시는?"

- **Learning Queries:**
  - "데이터 증강 기법 사용 예시 보여줘"
  - "Transformer 구현한 사람 있어?"

---

### 5. Analytics & Visualization Dashboard

**5.1 Real-time Leaderboard**

**현재 주간 랭킹:**

| 순위 | 이름 | 총점 | 코드 | 문서 | 품질 | 공유 |
|-----|------|------|------|------|------|------|
| 🥇 | 김철수 | 92 | 95 | 88 | 90 | 85 |
| 🥈 | 이영희 | 88 | 90 | 85 | 87 | 82 |
| 🥉 | 박민수 | 85 | 82 | 90 | 88 | 80 |
| 4 | 정수진 | 82 | 85 | 80 | 81 | 78 |
| ... | ... | ... | ... | ... | ... | ... |

**Ranking Algorithm:**

```python
total_score = (
    0.40 * code_contribution_score +
    0.30 * documentation_score +
    0.20 * code_quality_score +
    0.10 * knowledge_sharing_score
)

# 세부 계산
code_contribution = (commits * 2) + (LOC_added * 0.1) - (LOC_deleted * 0.05)
documentation = (docs_created * 10) + (docs_modified * 5)
quality = average(LLM_complexity_score, maintainability_index)
knowledge_sharing = (times_code_retrieved_in_RAG * 5)
```

**5.2 Individual Analytics Page**

**구성:**
- **Personal Metrics Over Time**
  - Line chart: 주간 코드 생산량 추이
  - Bar chart: 언어별 사용 분포
  - Activity heatmap (GitHub-style 기여 그래프)

- **Quality Trends**
  - 코드 품질 점수 변화
  - 복잡도 트렌드
  - 문서화율

- **Recent Contributions**
  - 최근 커밋 목록
  - 주요 변경 사항 요약
  - LLM 분석 하이라이트

**5.3 Team Analytics Dashboard**

- **Aggregate Productivity**
  - 전체 팀 주간 생산량
  - 월별/분기별 트렌드

- **Language Distribution**
  - Pie chart: 팀 전체 사용 언어 비율

- **Collaboration Network**
  - Graph visualization: 누가 누구 코드를 참조했는지
  - Knowledge flow diagram

- **Knowledge Sharing Metrics**
  - 가장 많이 검색된 코드 스니펫
  - 가장 도움이 된 팀원 (RAG 쿼리 기반)

**5.4 RAG Interface (Code Explorer)**

**UI Components:**

```
┌──────────────────────────────────────────────────────┐
│  🔍 Ask about your teammates' code...                │
│  [텍스트 입력창: "누가 데이터 전처리 파이프라인 만들었어?"] │
│  [🔎 Search]                                          │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  💬 AI Response:                                      │
│  3명의 팀원이 데이터 전처리 파이프라인을 구현했습니다:   │
│                                                       │
│  📌 김철수 (2025-10-10) - 추천 ⭐                     │
│  ```python                                            │
│  class DataPipeline:                                  │
│      def preprocess(self, data):                      │
│          # Pandas 기반, 확장 가능                      │
│  ```                                                  │
│  💡 Summary: 모듈화가 잘 되어 있고 에러 처리 포함        │
│  📊 Quality: 8.5/10  |  📂 View Full Code             │
│                                                       │
│  📌 이영희 (2025-09-28)                                │
│  ```python                                            │
│  def preprocess_batch(files, output_dir):             │
│      # 배치 처리에 최적화                              │
│  ```                                                  │
│  💡 Summary: 대용량 데이터 처리에 효율적                │
│  📊 Quality: 7.8/10  |  📂 View Full Code             │
│                                                       │
│  [💬 Ask follow-up question...]                       │
└──────────────────────────────────────────────────────┘
```

**Features:**
- Chat-like interface
- Syntax-highlighted code previews
- Author attribution with profile links
- Quality scores and recommendations
- Direct links to GitHub/GitLab repos
- Follow-up question capability

**5.5 Weekly Submission Form**

```
┌─────────────────────────────────────────────────────┐
│  📝 Weekly Productivity Report                      │
│  Week of: 2025-10-14 ~ 2025-10-20                   │
│                                                      │
│  📊 Auto-detected from Git (verify):                │
│  ✓ Commits: 15                                      │
│  ✓ Lines Added: 1,245                               │
│  ✓ Files Changed: 8                                 │
│                                                      │
│  ✏️ Manual Input:                                    │
│  Documents Created:  [3]                            │
│  Documents Modified: [5]                            │
│                                                      │
│  📓 Weekly Notes:                                    │
│  [Implemented transformer model for text            │
│   classification. Optimized training pipeline.      │
│   Documented API usage in README.]                  │
│                                                      │
│  [Submit Report] [Save Draft]                       │
└─────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack

### Backend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **API Framework** | FastAPI | Async support, auto-generated docs, WebSocket |
| **Task Queue** | Celery + Redis | Background processing for git sync & LLM analysis |
| **ORM** | SQLAlchemy | PostgreSQL interaction with type safety |
| **Git Integration** | GitPython | Programmatic git operations |
| **Vector DB Client** | qdrant-client | Python SDK for Qdrant |
| **LLM Integration** | LangChain | RAG orchestration, multi-LLM support |
| **Embedding** | OpenAI API | High-quality code embeddings |

### Frontend

| Option | Technology | Use Case |
|--------|------------|----------|
| **Option A (Recommended for MVP)** | Streamlit | Rapid prototyping, Python-native, easy deployment |
| **Option B (Production)** | React + TypeScript | Customizable, professional UI, better UX |
| **Charts** | Recharts / D3.js | Data visualization |
| **Real-time** | WebSocket | Live leaderboard updates |

### Data Storage

| Database | Purpose | Technology |
|----------|---------|------------|
| **Relational** | Users, metrics, rankings | PostgreSQL 15+ |
| **Vector** | Code embeddings | Qdrant (open-source, self-hosted) |
| **Cache** | Task queue, sessions | Redis |
| **File Storage** | Git clones, artifacts | Local FS or S3-compatible |

### LLM & Embeddings

| Component | Options | Recommendation |
|-----------|---------|----------------|
| **Code Analysis LLM** | GPT-4, Claude 3.5 Sonnet, CodeLlama | **Claude 3.5 Sonnet** (best code understanding) |
| **Embedding Model** | OpenAI text-embedding-3-small, local transformers | **OpenAI** (quality), fallback to local for privacy |
| **RAG Framework** | LangChain, LlamaIndex | **LangChain** (flexibility) |

### Deployment

```yaml
Development:
  - Docker Compose for all services
  - Local Qdrant instance
  - SQLite → PostgreSQL migration path

Production:
  - Kubernetes (if scaling needed)
  - Managed PostgreSQL (AWS RDS / Cloud SQL)
  - Qdrant on dedicated server
  - Nginx reverse proxy
  - SSL/TLS certificates
```

---

## 🔄 LLM Agent Workflow (Detailed)

### Phase 1: Git Monitoring & Extraction

**Scheduled Job (Daily/Weekly via Celery):**

```python
@celery.task
def sync_all_repos():
    users = db.query(User).filter(User.repo_url.isnot(None)).all()
    for user in users:
        sync_user_repo.delay(user.id)  # Parallel tasks

@celery.task
def sync_user_repo(user_id):
    user = db.query(User).get(user_id)
    repo = git.Repo.clone_from(user.repo_url, f'/tmp/repos/{user.id}')
    # Or git pull if already cloned

    # Get commits since last sync
    last_sync = get_last_sync_timestamp(user_id)
    commits = list(repo.iter_commits(since=last_sync))

    # Extract metrics
    metrics = analyze_commits(commits)
    store_git_metrics(user_id, metrics)

    # Trigger code analysis
    for commit in commits:
        analyze_commit_code.delay(user_id, commit.hexsha)
```

### Phase 2: Code Chunking

```python
def chunk_code_file(file_path, content):
    """Parse code into logical units using tree-sitter"""
    parser = get_parser(file_path)  # Language-specific
    tree = parser.parse(bytes(content, 'utf8'))

    chunks = []
    for node in tree.root_node.children:
        if node.type in ['function_definition', 'class_definition', 'method_definition']:
            chunk = {
                'type': node.type,
                'name': extract_name(node),
                'code': content[node.start_byte:node.end_byte],
                'start_line': node.start_point[0],
                'end_line': node.end_point[0],
                'docstring': extract_docstring(node)
            }
            chunks.append(chunk)
    return chunks
```

### Phase 3: LLM Analysis (Parallel)

```python
@celery.task
def analyze_code_chunk(user_id, chunk):
    """Analyze single code chunk with LLM"""
    prompt = f"""
    Analyze this {chunk['type']} code:

    ```{chunk['language']}
    {chunk['code']}
    ```

    Provide:
    1. One-sentence summary (what it does)
    2. Purpose (why it exists)
    3. Complexity score (1-10)
    4. Key algorithms/patterns used
    5. Quality assessment (maintainability, efficiency)

    Format as JSON.
    """

    response = llm.invoke(prompt)
    analysis = json.loads(response.content)

    # Store in database
    db.add(CodeAnalysis(
        user_id=user_id,
        file_path=chunk['file_path'],
        function_name=chunk['name'],
        analysis_summary=analysis['summary'],
        complexity_score=analysis['complexity'],
        quality_metrics=analysis
    ))
    db.commit()

    # Generate embedding
    generate_embedding.delay(user_id, chunk, analysis)
```

### Phase 4: Embedding Generation

```python
@celery.task
def generate_embedding(user_id, chunk, analysis):
    """Create vector embedding for code chunk"""
    # Combine code + summary for better retrieval
    text_to_embed = f"""
    Function: {chunk['name']}
    Summary: {analysis['summary']}
    Purpose: {analysis['purpose']}
    Code:
    {chunk['code']}
    """

    # Generate embedding
    embedding = openai.Embedding.create(
        model="text-embedding-3-small",
        input=text_to_embed
    )

    # Store in Qdrant
    qdrant_client.upsert(
        collection_name="code_embeddings",
        points=[{
            "id": generate_id(),
            "vector": embedding['data'][0]['embedding'],
            "payload": {
                "user_id": user_id,
                "user_name": get_user_name(user_id),
                "file_path": chunk['file_path'],
                "function_name": chunk['name'],
                "code_snippet": chunk['code'][:500],  # Truncate for storage
                "summary": analysis['summary'],
                "language": chunk['language'],
                "timestamp": chunk['timestamp'],
                "complexity_score": analysis['complexity']
            }
        }]
    )
```

### Phase 5: Knowledge Graph Building (Optional Enhancement)

```python
def build_knowledge_graph():
    """Identify relationships between code chunks"""
    # Find similar implementations
    all_chunks = db.query(CodeAnalysis).all()

    for chunk in all_chunks:
        # Search for similar code
        similar = qdrant_client.search(
            collection_name="code_embeddings",
            query_vector=chunk.embedding,
            limit=5,
            query_filter={"must_not": [{"key": "user_id", "match": {"value": chunk.user_id}}]}
        )

        # Store cross-references
        for match in similar:
            if match.score > 0.85:  # High similarity threshold
                db.add(CodeRelationship(
                    chunk_a=chunk.id,
                    chunk_b=match.id,
                    relationship_type="similar_implementation",
                    similarity_score=match.score
                ))
```

---

## 🔍 RAG Pipeline Implementation

### Query Handler

```python
class RAGQueryHandler:
    def __init__(self):
        self.qdrant = QdrantClient(url="http://localhost:6333")
        self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

    async def query(self, user_question: str, filters: dict = None):
        """Process user query and return synthesized response"""

        # Step 1: Query understanding
        intent = await self.understand_query(user_question)

        # Step 2: Hybrid retrieval
        vector_results = await self.vector_search(user_question, filters)
        keyword_results = await self.keyword_search(intent['keywords'])

        # Step 3: Rerank and merge
        top_results = self.rerank(vector_results, keyword_results, intent)

        # Step 4: Generate response
        response = await self.generate_response(user_question, top_results)

        # Step 5: Track for knowledge sharing metrics
        self.log_retrieval(top_results)

        return response

    async def vector_search(self, query: str, filters: dict):
        """Semantic search in Qdrant"""
        # Generate query embedding
        query_embedding = openai.Embedding.create(
            model="text-embedding-3-small",
            input=query
        )['data'][0]['embedding']

        # Build Qdrant filter
        qdrant_filter = self.build_filter(filters)

        # Search
        results = self.qdrant.search(
            collection_name="code_embeddings",
            query_vector=query_embedding,
            limit=20,
            query_filter=qdrant_filter
        )

        return results

    def rerank(self, vector_results, keyword_results, intent):
        """Combine and rerank results"""
        combined = []

        for result in vector_results:
            score = (
                result.score * 0.6 +  # Semantic relevance
                result.payload['complexity_score'] / 10 * 0.2 +  # Quality
                self.recency_score(result.payload['timestamp']) * 0.1 +
                self.diversity_score(result, combined) * 0.1
            )
            combined.append((score, result))

        combined.sort(key=lambda x: x[0], reverse=True)
        return [result for score, result in combined[:5]]

    async def generate_response(self, query: str, results):
        """LLM synthesizes answer from retrieved code"""
        context = self.format_context(results)

        prompt = f"""
        User question: {query}

        Here are relevant code examples from the research team:

        {context}

        Synthesize a helpful response that:
        1. Compares different approaches
        2. Highlights best practices
        3. Provides code examples with attribution
        4. Recommends which approach to use and why

        Format with markdown and code blocks.
        """

        response = await self.llm.ainvoke(prompt)
        return response.content

    def format_context(self, results):
        """Format retrieved code for LLM context"""
        context_parts = []

        for i, result in enumerate(results, 1):
            p = result.payload
            context_parts.append(f"""
**Example {i} - {p['user_name']} ({p['timestamp'][:10]})**
File: `{p['file_path']}`
Function: `{p['function_name']}`
Summary: {p['summary']}
Quality Score: {p['complexity_score']}/10

```{p['language']}
{p['code_snippet']}
```
""")

        return "\n\n---\n\n".join(context_parts)
```

---

## 📊 Implementation Roadmap

### MVP (Weeks 1-4) - Quick Win

**Goal:** Get basic monitoring working ASAP

**Features:**
- ✅ PostgreSQL setup with core tables
- ✅ Manual weekly submission form (web UI)
- ✅ Basic git metrics collection (GitPython)
- ✅ Simple leaderboard (no real-time, daily refresh)
- ✅ Individual profile pages with charts
- ✅ Admin dashboard for monitoring

**Tech Stack (MVP):**
- Backend: FastAPI
- Frontend: Streamlit (fastest)
- Database: PostgreSQL
- No vector DB yet
- No LLM analysis yet

**Deliverable:** Working productivity tracking system that lab members can start using

---

### Phase 2 (Weeks 5-6) - Automation

**Goal:** Reduce manual work with automation

**Features:**
- ✅ Celery + Redis for background tasks
- ✅ Automated git sync (daily scheduled)
- ✅ Real-time leaderboard updates (WebSocket)
- ✅ Email notifications for weekly submissions
- ✅ Longitudinal analytics (month-over-month trends)

**Deliverable:** Fully automated monitoring with minimal manual input

---

### Phase 3 (Weeks 7-8) - LLM Integration

**Goal:** Add intelligent code analysis

**Features:**
- ✅ LLM code analyzer (Claude 3.5 Sonnet)
- ✅ Automated code summarization
- ✅ Quality metrics generation
- ✅ Complexity analysis
- ✅ Store analysis in database
- ✅ Enhanced quality scoring in rankings

**Deliverable:** AI-powered code understanding and quality assessment

---

### Phase 4 (Weeks 9-10) - RAG System

**Goal:** Enable knowledge discovery

**Features:**
- ✅ Qdrant vector database setup
- ✅ Code embedding pipeline
- ✅ Semantic search implementation
- ✅ RAG query interface (chat UI)
- ✅ Knowledge sharing metrics
- ✅ Enhanced rankings with sharing score

**Deliverable:** Full RAG system for cross-member code discovery

---

### Phase 5 (Weeks 11-12) - Polish & Deploy

**Goal:** Production-ready system

**Features:**
- ✅ Performance optimization (caching, indexing)
- ✅ User acceptance testing
- ✅ Docker containerization
- ✅ Documentation and training materials
- ✅ Deployment to lab server
- ✅ Monitoring and logging

**Deliverable:** Stable production system

---

### Future Enhancements (Post-MVP)

- 🔮 **Code Review Assistant:** LLM suggests improvements for new commits
- 🔮 **Duplicate Detection:** Find redundant implementations across repos
- 🔮 **Skill Mapping:** Identify expertise areas per member
- 🔮 **Recommendation Engine:** "You might want to see X's implementation"
- 🔮 **Team Collaboration Graph:** Visualize knowledge flows
- 🔮 **Mobile App:** iOS/Android dashboard access
- 🔮 **Slack/Teams Integration:** Weekly digest notifications
- 🔮 **Export Features:** PDF reports, data downloads

---

## 🔐 Security & Privacy Considerations

### Access Control

```python
# Role-based access
ROLES = {
    "student": {
        "can_view_own_data": True,
        "can_view_team_rankings": True,
        "can_view_others_code": True,  # RAG queries
        "can_edit_own_submissions": True,
        "can_view_others_details": False
    },
    "advisor": {
        "can_view_all_data": True,
        "can_export_data": True,
        "can_manage_users": True,
        "can_view_analytics": True
    }
}
```

### Data Privacy

- **Internal Network Only:** System accessible only within lab VPN
- **Anonymous RAG Option:** Option to anonymize code authors in RAG results
- **Git Repo Permissions:** Requires authentication for private repos
- **Secure Storage:** Encrypted database backups
- **Audit Logs:** Track who accessed what data

### Compliance

- **GDPR/CCPA Considerations:**
  - Users can request data deletion
  - Clear consent for data collection
  - Transparent data usage policies

- **Academic Ethics:**
  - No public ranking (internal only)
  - Opt-in for RAG knowledge sharing
  - Attribution in code examples

---

## 📈 Success Metrics

### System Usage

- **Adoption Rate:** % of lab members submitting weekly (target: >90%)
- **RAG Query Volume:** Average queries per user per week (target: >5)
- **Code Coverage:** % of repos successfully analyzed (target: >95%)

### Knowledge Sharing

- **Cross-pollination:** # of times code from member A helps member B
- **Duplicate Reduction:** % decrease in redundant implementations
- **Learning Velocity:** Time to find relevant code examples (target: <2 min)

### Productivity Impact

- **Submission Compliance:** Weekly submission rate
- **Code Quality Trend:** Average quality scores over time
- **Documentation Coverage:** % of code with adequate docs

---

## 🚀 Quick Start Guide (for Implementation)

### Step 1: Environment Setup

```bash
# Clone project structure
mkdir lab-knowledge-system
cd lab-knowledge-system

# Backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary celery redis qdrant-client langchain openai gitpython

# Database
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=lab123 postgres:15
docker run -d -p 6333:6333 qdrant/qdrant

# Redis
docker run -d -p 6379:6379 redis:7
```

### Step 2: Initialize Database

```bash
python scripts/init_db.py  # Creates tables
python scripts/seed_users.py  # Add lab members
```

### Step 3: Configure Git Access

```python
# config.py
MEMBER_REPOS = [
    {"name": "김철수", "github": "username1", "repo": "https://github.com/lab/member1"},
    {"name": "이영희", "github": "username2", "repo": "https://github.com/lab/member2"},
    # ... 20 members
]
```

### Step 4: Start Services

```bash
# Terminal 1: API
uvicorn app.main:app --reload

# Terminal 2: Celery worker
celery -A app.tasks worker --loglevel=info

# Terminal 3: Dashboard
streamlit run dashboard.py
```

### Step 5: First Sync

```bash
curl -X POST http://localhost:8000/admin/sync-all-repos
```

---

## 📚 References & Further Reading

### Vector Databases
- Qdrant Documentation: https://qdrant.tech/documentation/
- Vector Database Comparison: https://github.com/erikbern/ann-benchmarks

### RAG Systems
- LangChain RAG Tutorial: https://python.langchain.com/docs/use_cases/question_answering/
- Building Production RAG: https://www.anthropic.com/research/building-effective-agents

### Code Analysis
- Tree-sitter (AST parsing): https://tree-sitter.github.io/tree-sitter/
- CodeBERT embeddings: https://github.com/microsoft/CodeBERT

### Research Papers
- "CodeSearchNet: Evaluating Code Search" (GitHub, 2019)
- "Retrieval-Augmented Generation for Code" (Meta AI, 2023)
- "Knowledge Distillation in Neural Networks" (Hinton et al., 2015)

---

## 📞 Contact & Support

**System Administrator:** [Lab Manager Name]
**Technical Lead:** [Developer Name]
**Slack Channel:** #lab-knowledge-system
**Issue Tracker:** [GitHub Issues URL]

---

## ✅ Conclusion

이 시스템은 연구실 구성원들의 생산성을 체계적으로 추적하고, LLM과 RAG 기술을 활용하여 팀 전체의 코드 지식을 공유 가능한 자산으로 전환합니다.

**핵심 가치:**
1. **투명성:** 모든 구성원이 자신의 기여도를 실시간으로 확인
2. **학습 가속:** 다른 사람의 우수 사례를 즉시 발견하고 학습
3. **지식 보존:** 개인의 코드 경험이 팀의 집단 지식으로 축적
4. **동기부여:** 건강한 경쟁과 인정을 통한 지속적 개선

**Next Steps:**
1. MVP 개발 착수 (4주 목표)
2. Pilot 테스트 with 5-10 members
3. 피드백 수렴 및 개선
4. Full deployment to 20+ members

**Implementation support 필요 시 언제든지 문의하세요!** 🚀
