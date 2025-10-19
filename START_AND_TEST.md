# Code-Monitor 시작 및 테스트 가이드

## 🚀 빠른 시작 (5단계)

### Step 1: Docker Desktop 시작
```bash
# macOS: Applications에서 Docker 실행
# 또는 터미널에서
open -a Docker

# Docker가 실행되었는지 확인
docker ps
```

**확인사항:** Docker Desktop 아이콘이 상태 표시줄에 나타나고 초록색이어야 합니다.

### Step 2: 데이터베이스 시작
```bash
cd /Users/jiookcha/Documents/git/Code-Monitor

# PostgreSQL + Redis 시작
docker-compose up -d

# 상태 확인 (healthy 상태 대기)
docker-compose ps

# 로그 확인 (문제 발생시)
docker-compose logs -f
```

**기대 출력:**
```
NAME                        STATUS              PORTS
code-monitor-postgres       Up (healthy)        0.0.0.0:5432->5432/tcp
code-monitor-redis          Up (healthy)        0.0.0.0:6379->6379/tcp
```

### Step 3: 데이터베이스 초기화
```bash
# 프로젝트 루트에서
python scripts/init_db.py
```

**기대 출력:**
```
🔧 Initializing Code-Monitor database...
✅ Complete!
   - users
   - weekly_submissions
   - git_metrics
   - rankings
   - code_analysis
```

### Step 4: Backend API 시작
```bash
# 새 터미널 열기
cd /Users/jiookcha/Documents/git/Code-Monitor/backend

# 가상환경 활성화 (아직 안했다면)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (처음만)
pip install -r requirements.txt

# API 시작
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**확인:**
- 브라우저에서 http://localhost:8000/docs 접속
- Swagger UI가 보이면 성공!

### Step 5: 통합 테스트 실행
```bash
# 새 터미널에서
cd /Users/jiookcha/Documents/git/Code-Monitor

# Python 테스트 (추천)
python scripts/test_system.py

# 또는 Bash 테스트
./scripts/test_api.sh
```

## 📊 테스트 결과 예시

```
🧪 Code-Monitor Integration Test Suite
==================================================

🔍 Pre-flight checks...
✅ API is running

Testing: Health Check
✅ PASSED
{
  "status": "healthy",
  "database": "connected"
}

Testing: Create User: 김철수
✅ PASSED
   User ID: 1

Testing: Create User: 이영희
✅ PASSED
   User ID: 2

Testing: List All Users
✅ PASSED
   Total users: 2
   - 김철수 (chulsu@lab.com)
   - 이영희 (younghee@lab.com)

Testing: Create Submission (User 1)
✅ PASSED
   Lines: 500, Docs: 3

Testing: Create Submission (User 2)
✅ PASSED
   Lines: 800, Docs: 5

Testing: Update Rankings
✅ PASSED
   Updated: 2 users

Testing: Get Current Week Rankings
✅ PASSED

   🏆 Leaderboard:
   1. 이영희: 90.0 points
      📊 P:80.0 Q:0.0 C:10.0
   2. 김철수: 65.0 points
      📊 P:50.0 Q:0.0 C:15.0

==================================================
Tests Passed: 8
Tests Failed: 0
==================================================

✅ All tests passed!
```

## 🌐 접속 URL

| 서비스 | URL | 설명 |
|--------|-----|------|
| API Root | http://localhost:8000 | API 기본 정보 |
| Swagger UI | http://localhost:8000/docs | 대화형 API 문서 |
| ReDoc | http://localhost:8000/redoc | 읽기 전용 API 문서 |
| Health Check | http://localhost:8000/health | 시스템 상태 확인 |
| Dashboard | http://localhost:8501 | Streamlit 대시보드 (선택) |

## 🧪 수동 API 테스트 (Swagger UI)

1. http://localhost:8000/docs 접속
2. 각 엔드포인트 확장
3. "Try it out" 클릭
4. 파라미터 입력
5. "Execute" 클릭
6. 결과 확인

**추천 테스트 순서:**
1. `GET /health` - 시스템 상태 확인
2. `POST /api/users` - 사용자 생성
3. `GET /api/users` - 사용자 목록 조회
4. `POST /api/users/{user_id}/submissions` - 주간 제출
5. `POST /api/rankings/update/{week_start_date}` - 랭킹 업데이트
6. `GET /api/rankings/current` - 현재 랭킹 조회

## 🎭 선택사항: Dashboard 시작

```bash
# 새 터미널
cd /Users/jiookcha/Documents/git/Code-Monitor/frontend

# 의존성 설치 (처음만)
pip install -r requirements.txt

# Dashboard 시작
streamlit run streamlit_app.py
```

**확인:** http://localhost:8501 접속

## 🔄 선택사항: Celery 시작

### Celery Worker (백그라운드 작업)
```bash
# 새 터미널
cd /Users/jiookcha/Documents/git/Code-Monitor/backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

### Celery Beat (스케줄러)
```bash
# 새 터미널
cd /Users/jiookcha/Documents/git/Code-Monitor/backend
source venv/bin/activate
celery -A app.core.celery_app beat --loglevel=info
```

**기능:**
- 매일 자동으로 Git repository 동기화
- 매주 자동으로 랭킹 업데이트

## 🐛 트러블슈팅

### 1. Docker 연결 실패
```bash
# Docker Desktop이 실행 중인지 확인
docker ps

# 안되면 Docker Desktop 재시작
# macOS: Applications에서 Docker 종료 후 재시작
```

### 2. 포트 충돌
```bash
# 사용 중인 프로세스 확인
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
uvicorn app.main:app --reload --port 8001
```

### 3. Database 연결 실패
```bash
# PostgreSQL 로그 확인
docker-compose logs postgres

# 컨테이너 재시작
docker-compose restart postgres

# 완전 재시작
docker-compose down
docker-compose up -d
```

### 4. Import 에러
```bash
# PYTHONPATH 설정
export PYTHONPATH=/Users/jiookcha/Documents/git/Code-Monitor/backend:$PYTHONPATH

# 또는 backend 디렉토리에서 실행
cd backend
python -m pytest tests/
```

## 📈 테스트 체크리스트

- [ ] Docker Desktop 실행 중
- [ ] `docker-compose ps` 모든 서비스 healthy
- [ ] `python scripts/init_db.py` 성공
- [ ] Backend API 실행 (`uvicorn app.main:app`)
- [ ] http://localhost:8000/docs 접속 가능
- [ ] http://localhost:8000/health 응답 "healthy"
- [ ] `python scripts/test_system.py` 모든 테스트 통과
- [ ] Swagger UI에서 API 동작 확인
- [ ] (선택) Dashboard 실행 및 접속

## 🎯 다음 단계

1. **Phase 4: Advanced Dashboard**
   - Rankings 시각화
   - 차트 및 트렌드
   - 실시간 리더보드

2. **Phase 5: LLM 통합**
   - 코드 분석
   - 자동 리뷰

3. **Phase 6: RAG System**
   - Vector DB (Qdrant)
   - 코드 검색

## 📚 추가 문서

- [TEST_GUIDE.md](./TEST_GUIDE.md) - 상세 테스트 가이드
- [README_QUICKSTART.md](./README_QUICKSTART.md) - 빠른 시작 가이드
- [lab-knowledge-system-design.md](./lab-knowledge-system-design.md) - 시스템 설계 문서
