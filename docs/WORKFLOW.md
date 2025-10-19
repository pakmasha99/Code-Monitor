# Code-Monitor 운영 워크플로우

## 📋 목차
1. [초기 설정 (한번만)](#1-초기-설정-한번만)
2. [학생 등록 및 Git Repo 연결](#2-학생-등록-및-git-repo-연결)
3. [일일/주간 자동 운영](#3-일일주간-자동-운영)
4. [학생 사용 워크플로우](#4-학생-사용-워크플로우)
5. [관리자 모니터링](#5-관리자-모니터링)

---

## 1. 초기 설정 (한번만)

### Step 1.1: 시스템 설치 및 구동

```bash
# 1. Docker 서비스 시작 (PostgreSQL, Redis, Qdrant)
docker-compose up -d

# 2. 데이터베이스 스키마 생성
python scripts/init_db.py

# 3. 백엔드 API 서버 시작
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Celery 워커 시작 (백그라운드 작업)
celery -A app.tasks worker --loglevel=info

# 5. 대시보드 시작
cd frontend
streamlit run streamlit_app.py
```

**결과:**
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- Database: PostgreSQL running
- Vector DB: Qdrant running

---

## 2. 학생 등록 및 Git Repo 연결

### Step 2.1: 학생 계정 생성

**Option A: 관리자 대시보드 사용**
```
Dashboard → Admin → Add User
- Name: 김철수
- Email: student1@lab.com
- GitHub Username: student1_github
- Role: student
```

**Option B: 스크립트 사용**
```python
# scripts/add_users.py
python scripts/add_users.py --csv students.csv
```

`students.csv` 예시:
```csv
name,email,github_username,repo_url
김철수,student1@lab.com,student1,https://github.com/lab-internal/student1-research
이영희,student2@lab.com,student2,https://github.com/lab-internal/student2-research
박민수,student3@lab.com,student3,https://github.com/lab-internal/student3-research
```

### Step 2.2: Git Repository 접근 설정

**중요:** 시스템이 학생들의 private repo에 접근할 수 있어야 합니다.

**Option A: GitHub Personal Access Token (PAT)**

1. GitHub에서 조직 전체 읽기 권한 PAT 생성
2. `.env` 파일에 추가:
```bash
GITHUB_ACCESS_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

3. 시스템이 자동으로 인증된 접근 사용

**Option B: SSH Keys**

1. 시스템 서버에 SSH 키 생성
2. 각 학생 repo에 Deploy Key로 등록
3. SSH URL 사용: `git@github.com:lab/student1.git`

**Option C: Internal GitLab/Gitea (추천)**

- 연구실 내부 Git 서버 사용
- 관리자 계정으로 모든 repo 접근 가능
- 외부 인증 불필요

### Step 2.3: 초기 Repo 동기화

```bash
# 모든 학생 repo를 처음으로 클론
curl -X POST http://localhost:8000/admin/sync-all-repos
```

**내부 동작:**
```
1. 시스템이 각 학생의 repo_url에서 git clone 수행
   → /tmp/repos/user_1/ 에 저장
   → /tmp/repos/user_2/ 에 저장

2. Git history 전체 분석
   - 모든 커밋 메타데이터 추출
   - 코드 변경량 계산
   - 언어별 통계 수집

3. 데이터베이스에 저장
   → git_metrics 테이블에 주별 집계 저장
```

---

## 3. 일일/주간 자동 운영

### 자동화 파이프라인 (매일 새벽 2시)

```
┌─────────────────────────────────────────────────────────┐
│  Celery Beat (스케줄러) - 매일 02:00 AM                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Task 1: Git Sync (모든 학생 repo git pull)              │
│  - 각 repo를 최신 상태로 업데이트                          │
│  - 새로운 커밋 감지                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Task 2: Git Metrics Extraction (병렬 처리)              │
│  - 지난 sync 이후 새로운 커밋 분석                         │
│  - Diff 분석: 추가/삭제 라인 수                           │
│  - 파일 변경 목록                                         │
│  - 언어별 통계                                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Task 3: Code Analysis (LLM 분석 - 병렬)                 │
│  - 변경된 코드 파일만 선택적 분석                          │
│  - tree-sitter로 함수/클래스 단위 파싱                    │
│  - 각 코드 청크를 LLM에 전송                              │
│  - 요약, 복잡도, 품질 평가 받음                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Task 4: Embedding Generation (병렬)                     │
│  - 코드 + LLM 요약 결합하여 텍스트 생성                    │
│  - OpenAI embedding API 호출                             │
│  - Qdrant에 벡터 저장 (메타데이터 포함)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Task 5: Weekly Aggregation (주 단위 집계)               │
│  - 이번 주 데이터 집계 (월~일)                            │
│  - 각 학생별 메트릭 계산                                  │
│  - 랭킹 점수 계산 및 순위 매김                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Task 6: Dashboard Update (실시간 갱신)                  │
│  - WebSocket으로 대시보드에 알림 전송                     │
│  - 캐시 무효화 및 새 데이터 로드                          │
└─────────────────────────────────────────────────────────┘
```

### 실제 동작 예시 (학생 1명 기준)

```python
# 1. Git Sync
@celery.task
def sync_user_repo(user_id=1):
    user = db.get_user(1)  # 김철수
    repo_path = "/tmp/repos/user_1"

    if os.path.exists(repo_path):
        # 기존 repo → git pull
        repo = git.Repo(repo_path)
        origin = repo.remotes.origin
        origin.pull()
    else:
        # 처음 → git clone
        repo = git.Repo.clone_from(user.repo_url, repo_path)

    # 마지막 sync 시각 이후 커밋 가져오기
    last_sync = get_last_sync_time(user_id)  # 2025-10-18 02:00:00
    new_commits = list(repo.iter_commits(since=last_sync))
    # → 5개 새 커밋 발견

    return new_commits

# 2. Metrics Extraction
@celery.task
def analyze_commits(user_id=1, commits):
    total_lines_added = 0
    total_lines_deleted = 0
    files_changed = set()
    languages = defaultdict(int)

    for commit in commits:
        # 각 커밋의 diff 분석
        for diff in commit.diff(commit.parents[0] if commit.parents else NULL_TREE):
            # 변경 파일
            files_changed.add(diff.a_path or diff.b_path)

            # 라인 수 계산
            if diff.diff:
                lines = diff.diff.decode('utf-8', errors='ignore').split('\n')
                added = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
                deleted = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))

                total_lines_added += added
                total_lines_deleted += deleted

                # 언어 감지
                ext = os.path.splitext(diff.a_path or diff.b_path)[1]
                lang = get_language(ext)  # .py → Python
                languages[lang] += added

    # 주간 메트릭 저장
    week_start = get_current_week_start()  # 2025-10-14 (월요일)
    db.save_git_metrics(
        user_id=user_id,
        week_start_date=week_start,
        commits_count=len(commits),  # 5
        files_changed=len(files_changed),  # 8
        lines_added=total_lines_added,  # 1245
        lines_deleted=total_lines_deleted,  # 234
        languages_breakdown=dict(languages)  # {"Python": 980, "JavaScript": 265}
    )

# 3. Code Analysis (변경된 파일만)
@celery.task
def analyze_changed_files(user_id=1, files_changed):
    for file_path in files_changed:
        if not is_code_file(file_path):
            continue

        # 파일 내용 읽기
        full_path = f"/tmp/repos/user_{user_id}/{file_path}"
        with open(full_path, 'r') as f:
            content = f.read()

        # tree-sitter로 함수/클래스 추출
        chunks = parse_code_into_chunks(file_path, content)
        # → [
        #     {"type": "function", "name": "preprocess_data", "code": "def preprocess_data(df):\n    ..."},
        #     {"type": "class", "name": "DataPipeline", "code": "class DataPipeline:\n    ..."}
        #   ]

        for chunk in chunks:
            # LLM 분석 (비동기)
            analyze_code_chunk.delay(user_id, file_path, chunk)

@celery.task
def analyze_code_chunk(user_id, file_path, chunk):
    # Claude API 호출
    prompt = f"""
    Analyze this {chunk['type']} in Python:

    ```python
    {chunk['code']}
    ```

    Provide JSON with:
    - summary: one-sentence description
    - purpose: why this exists
    - complexity: 1-10 score
    - quality: maintainability assessment
    """

    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}]
    )

    analysis = json.loads(response.content[0].text)
    # → {
    #     "summary": "Preprocesses DataFrame by handling missing values and normalizing features",
    #     "purpose": "Data cleaning pipeline before model training",
    #     "complexity": 6,
    #     "quality": "Good modular design, could use more error handling"
    #   }

    # 데이터베이스 저장
    db.save_code_analysis(
        user_id=user_id,
        file_path=file_path,
        function_name=chunk['name'],
        analysis_summary=analysis['summary'],
        complexity_score=analysis['complexity'],
        quality_metrics=analysis
    )

    # 임베딩 생성 트리거
    generate_embedding.delay(user_id, file_path, chunk, analysis)

# 4. Embedding Generation
@celery.task
def generate_embedding(user_id, file_path, chunk, analysis):
    # 코드 + 요약 결합 (검색 품질 향상)
    text_to_embed = f"""
    Function: {chunk['name']}
    Summary: {analysis['summary']}
    Purpose: {analysis['purpose']}

    Code:
    {chunk['code']}
    """

    # OpenAI embedding API
    response = openai.Embedding.create(
        model="text-embedding-3-small",
        input=text_to_embed
    )

    vector = response['data'][0]['embedding']  # 1536 차원

    # Qdrant에 저장
    qdrant_client.upsert(
        collection_name="code_embeddings",
        points=[{
            "id": f"{user_id}_{file_path}_{chunk['name']}",
            "vector": vector,
            "payload": {
                "user_id": user_id,
                "user_name": "김철수",
                "file_path": file_path,
                "function_name": chunk['name'],
                "code_snippet": chunk['code'][:500],
                "summary": analysis['summary'],
                "language": "Python",
                "complexity_score": analysis['complexity'],
                "timestamp": datetime.now().isoformat()
            }
        }]
    )

# 5. Weekly Ranking Calculation
@celery.task
def calculate_weekly_rankings():
    week_start = get_current_week_start()
    users = db.get_all_users()

    scores = []
    for user in users:
        # 각 학생의 이번 주 메트릭
        git_metrics = db.get_git_metrics(user.id, week_start)
        submission = db.get_weekly_submission(user.id, week_start)
        code_quality = db.get_avg_quality_score(user.id, week_start)
        sharing_score = db.get_knowledge_sharing_score(user.id, week_start)

        # 점수 계산
        code_score = (git_metrics.commits_count * 2) + (git_metrics.lines_added * 0.1)
        doc_score = (submission.documents_created * 10) + (submission.documents_modified * 5)

        total_score = (
            code_score * 0.4 +
            doc_score * 0.3 +
            code_quality * 0.2 +
            sharing_score * 0.1
        )

        scores.append((user.id, total_score))

    # 정렬 및 순위 부여
    scores.sort(key=lambda x: x[1], reverse=True)

    for rank, (user_id, score) in enumerate(scores, 1):
        db.save_ranking(
            user_id=user_id,
            week_start_date=week_start,
            total_score=score,
            rank_position=rank
        )
```

---

## 4. 학생 사용 워크플로우

### Workflow 1: 주간 리포트 제출 (매주 일요일)

```
학생 로그인
    ↓
대시보드에서 "Submit Weekly Report" 클릭
    ↓
┌─────────────────────────────────────────────┐
│  주간 리포트 작성 폼                         │
│                                              │
│  📊 자동 감지된 Git 메트릭 (확인용):          │
│  ✓ Commits: 15                              │
│  ✓ Lines Added: 1,245                       │
│  ✓ Files Changed: 8                         │
│                                              │
│  ✏️ 수동 입력:                               │
│  문서 생성: [3]                              │
│  문서 수정: [5]                              │
│                                              │
│  📓 이번 주 작업 노트:                        │
│  [Transformer 모델 구현 완료.                │
│   데이터 전처리 파이프라인 최적화.            │
│   API 문서 작성.]                            │
│                                              │
│  [Submit] [Save Draft]                      │
└─────────────────────────────────────────────┘
    ↓
제출 완료
    ↓
자동으로 랭킹 재계산
    ↓
대시보드 실시간 업데이트 (WebSocket)
```

### Workflow 2: 코드 검색 (RAG 사용)

```
학생이 다른 사람 코드 찾고 싶을 때
    ↓
대시보드 "Code Explorer" 탭
    ↓
┌─────────────────────────────────────────────┐
│  🔍 질문 입력:                               │
│  "누가 데이터 전처리 파이프라인 만들었어?"    │
│  [🔎 Search]                                 │
└─────────────────────────────────────────────┘
    ↓
백엔드 RAG 파이프라인 실행:
    1. 질문 임베딩 생성
    2. Qdrant 벡터 검색 (의미적 유사도)
    3. Top-5 코드 스니펫 검색
    4. 관련성 재정렬
    5. LLM에게 컨텍스트 제공
    6. 종합 응답 생성
    ↓
┌─────────────────────────────────────────────┐
│  💬 AI 응답:                                 │
│  3명이 데이터 전처리 파이프라인을 구현했어요: │
│                                              │
│  📌 김철수 (2025-10-10) - 추천 ⭐            │
│  ```python                                   │
│  class DataPipeline:                         │
│      def preprocess(self, df):               │
│          # Pandas 기반, 확장 가능             │
│          ...                                 │
│  ```                                         │
│  💡 모듈화가 잘 되어있고 에러처리 포함        │
│  📊 Quality: 8.5/10                          │
│  📂 [View Full File]                         │
│                                              │
│  📌 이영희 (2025-09-28)                      │
│  [Similar format...]                         │
│                                              │
│  💬 [Ask follow-up question...]              │
└─────────────────────────────────────────────┘
    ↓
학생이 코드 참고 및 학습
    ↓
(시스템이 knowledge_sharing_score 증가 기록)
```

---

## 5. 관리자 모니터링

### 대시보드 주요 뷰

**View 1: 실시간 Leaderboard**
```
┌──────────────────────────────────────────────┐
│  🏆 이번 주 랭킹 (2025-10-14 ~ 10-20)         │
│                                               │
│  1. 🥇 김철수   92점  (↑2)                    │
│      Code: 95 | Docs: 88 | Quality: 90       │
│                                               │
│  2. 🥈 이영희   88점  (→)                     │
│      Code: 90 | Docs: 85 | Quality: 87       │
│                                               │
│  3. 🥉 박민수   85점  (↓1)                    │
│      Code: 82 | Docs: 90 | Quality: 88       │
│  ...                                          │
│                                               │
│  [Export CSV] [View Trends]                  │
└──────────────────────────────────────────────┘
```

**View 2: Team Analytics**
```
┌──────────────────────────────────────────────┐
│  📈 팀 전체 생산성 트렌드                      │
│                                               │
│  (Line Chart: 주별 평균 코드 생산량)           │
│  Week 40: 850 LOC/person                     │
│  Week 41: 920 LOC/person  ↑ 8.2%             │
│  Week 42: 1050 LOC/person ↑ 14.1%            │
│                                               │
│  📊 언어 분포:                                │
│  (Pie Chart)                                 │
│  Python: 65%                                 │
│  JavaScript: 20%                             │
│  C++: 10%                                    │
│  Other: 5%                                   │
│                                               │
│  🤝 지식 공유 활동:                           │
│  이번 주 RAG 쿼리: 145건                      │
│  가장 많이 참조된 코드: 김철수의 transformer.py │
└──────────────────────────────────────────────┘
```

---

## 6. 트러블슈팅 시나리오

### Q1: 학생이 새 repo를 만들었어요

```bash
# 1. 데이터베이스에서 학생 정보 업데이트
curl -X PATCH http://localhost:8000/users/5 \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/lab/student5-new-repo"}'

# 2. 해당 학생만 초기 sync
curl -X POST http://localhost:8000/admin/sync-user-repo/5
```

### Q2: 특정 학생 데이터가 이상해요

```bash
# 1. 해당 학생의 로컬 repo 삭제
rm -rf /tmp/repos/user_5

# 2. 재동기화 (처음부터 다시 클론)
curl -X POST http://localhost:8000/admin/sync-user-repo/5?force=true

# 3. 재분석 트리거
curl -X POST http://localhost:8000/admin/reanalyze-user/5
```

### Q3: LLM 분석이 너무 느려요

```bash
# Celery worker 수 증가 (병렬 처리)
celery -A app.tasks worker --concurrency=10 --loglevel=info
```

### Q4: Qdrant에 벡터가 너무 많아요

```python
# 오래된 데이터 정리 (6개월 이전)
python scripts/cleanup_old_vectors.py --older-than=6m
```

---

## 7. 데이터 흐름 요약

```
학생 Git Repo (20개)
    ↓ (Daily Sync)
Local Git Clones (/tmp/repos/user_*)
    ↓ (Parsing)
Code Chunks (함수/클래스)
    ↓ (LLM Analysis)
PostgreSQL (code_analysis 테이블)
    +
    ↓ (Embedding)
Qdrant Vector DB (code_embeddings 컬렉션)
    ↓ (RAG Query)
학생 질문 → 의미적 검색 → 관련 코드 발견
    ↓ (LLM Synthesis)
종합 응답 with 코드 예시
```

---

## 8. 주요 파일 및 위치

| 데이터 | 저장 위치 | 용도 |
|--------|-----------|------|
| Git Repos | `/tmp/repos/user_*` | 소스 코드 원본 |
| PostgreSQL | Docker volume `postgres_data` | 메트릭, 랭킹, 분석 |
| Qdrant | Docker volume `qdrant_storage` | 코드 임베딩 벡터 |
| Logs | `logs/celery.log`, `logs/api.log` | 디버깅 |
| Backups | `backups/` (cron job) | 주간 DB 백업 |

---

## 9. 성능 고려사항

- **Git Sync**: 20명 × 평균 100MB repo = ~2GB 디스크
- **LLM 분석**: 학생당 주 10개 파일 × 5분 = 50분 (병렬 처리 시 5분)
- **Embedding 생성**: OpenAI API 비용 고려 (월 ~$50 예상)
- **Vector 저장**: 함수당 1.5KB × 1000함수/학생 × 20명 = ~30MB

---

이 워크플로우대로 진행하면 완전히 자동화된 시스템이 됩니다!

**가장 중요한 것:**
1. 학생 repo 접근 권한 확보
2. API 키 설정 (OpenAI, Anthropic)
3. 스케줄러 설정 (매일 자동 실행)

질문 있으시면 언제든 물어보세요! 🚀
