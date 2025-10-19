# Code-Monitor 통합 테스트 가이드

## 📋 사전 요구사항

### 1. Docker Desktop
- **확인**: `docker --version`
- **설치**: https://www.docker.com/products/docker-desktop

### 2. Python 환경
- Python 3.10+
- 가상환경 (venv)

### 3. 필수 패키지
```bash
cd backend
pip install -r requirements.txt
```

## 🚀 시스템 시작 순서

### Step 1: Docker 서비스 시작
```bash
cd /Users/jiookcha/Documents/git/Code-Monitor

# Docker Desktop 실행 확인
docker ps

# PostgreSQL + Redis 시작
docker-compose up -d

# 서비스 확인 (healthy 상태 확인)
docker-compose ps
```

**기대 출력:**
```
NAME                        STATUS              PORTS
code-monitor-postgres       Up (healthy)        0.0.0.0:5432->5432/tcp
code-monitor-redis          Up (healthy)        0.0.0.0:6379->6379/tcp
```

### Step 2: 데이터베이스 초기화
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

### Step 3: Backend API 시작
```bash
# 터미널 1
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**확인:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Step 4: Celery Worker 시작 (선택적)
```bash
# 터미널 2
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

### Step 5: Celery Beat 시작 (선택적)
```bash
# 터미널 3
cd backend
source venv/bin/activate
celery -A app.core.celery_app beat --loglevel=info
```

### Step 6: Dashboard 시작 (선택적)
```bash
# 터미널 4
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**확인:**
- Dashboard: http://localhost:8501

## 🧪 API 테스트 시나리오

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

**기대 결과:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Test 2: User 생성
```bash
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "김철수",
    "email": "test1@lab.com",
    "github_username": "test_user1",
    "repo_url": "https://github.com/test/repo1",
    "role": "student"
  }'
```

**기대 결과:**
```json
{
  "id": 1,
  "name": "김철수",
  "email": "test1@lab.com",
  "github_username": "test_user1",
  "repo_url": "https://github.com/test/repo1",
  "role": "student",
  "is_active": true
}
```

### Test 3: User 목록 조회
```bash
curl http://localhost:8000/api/users
```

### Test 4: Weekly Submission 생성
```bash
curl -X POST "http://localhost:8000/api/users/1/submissions" \
  -H "Content-Type: application/json" \
  -d '{
    "week_start_date": "2025-10-13",
    "code_lines_added": 500,
    "documents_created": 3,
    "notes": "Implemented authentication system"
  }'
```

### Test 5: Git Metrics 생성 (시뮬레이션)
```bash
# Python으로 직접 생성
python << 'EOF'
from datetime import date
from backend.app.core.database import SessionLocal
from backend.app.models.git_metrics import GitMetrics

db = SessionLocal()
metrics = GitMetrics(
    user_id=1,
    week_start_date=date(2025, 10, 13),
    commits_count=15,
    lines_added=800,
    lines_deleted=200,
    files_changed=25,
    languages_breakdown={"Python": 600, "JavaScript": 200}
)
db.add(metrics)
db.commit()
print("✅ Git metrics created")
db.close()
EOF
```

### Test 6: Rankings 업데이트
```bash
curl -X POST "http://localhost:8000/api/rankings/update/2025-10-13"
```

**기대 결과:**
```json
{
  "status": "success",
  "total_users": 1,
  "updated": 1,
  "week_start_date": "2025-10-13"
}
```

### Test 7: Rankings 조회
```bash
# 현재 주 랭킹
curl http://localhost:8000/api/rankings/current

# 특정 주 랭킹
curl http://localhost:8000/api/rankings/week/2025-10-13

# Top 3 performers
curl "http://localhost:8000/api/rankings/top/3?week_start_date=2025-10-13"

# 사용자 히스토리
curl "http://localhost:8000/api/users/1/ranking/history?weeks=4"
```

## 🎭 Playwright를 이용한 Dashboard 테스트

### 1. Playwright 설정
```bash
# MCP server 사용 (이미 설정되어 있음)
# Chrome DevTools Protocol 기반 브라우저 자동화
```

### 2. Dashboard 접속 테스트
- URL: http://localhost:8501
- 페이지: Home, Users, Add User, Status
- 기능: User 추가, 목록 조회, Health 체크

### 3. API Swagger UI 테스트
- URL: http://localhost:8000/docs
- 모든 엔드포인트 대화형 테스트 가능

## 📊 테스트 체크리스트

- [ ] Docker 서비스 실행 (PostgreSQL + Redis)
- [ ] 데이터베이스 초기화 완료
- [ ] Backend API 실행 및 health check 성공
- [ ] User 생성/조회 API 동작 확인
- [ ] Weekly Submission 생성/조회 동작 확인
- [ ] Git Metrics 데이터 생성 확인
- [ ] Rankings 계산 및 조회 동작 확인
- [ ] Dashboard 접속 및 기본 기능 확인
- [ ] Celery Worker 실행 (선택적)
- [ ] Celery Beat 실행 (선택적)

## 🐛 트러블슈팅

### Docker 연결 실패
```bash
# Docker Desktop이 실행 중인지 확인
# macOS: Applications에서 Docker 실행
# Windows: Docker Desktop 실행
```

### Database 연결 실패
```bash
# PostgreSQL 컨테이너 로그 확인
docker-compose logs postgres

# 컨테이너 재시작
docker-compose restart postgres
```

### Port 충돌
```bash
# 사용 중인 포트 확인
lsof -i :8000  # Backend
lsof -i :8501  # Dashboard
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# 프로세스 종료
kill -9 <PID>
```

### Import 에러
```bash
# PYTHONPATH 설정 확인
export PYTHONPATH=/Users/jiookcha/Documents/git/Code-Monitor/backend:$PYTHONPATH

# 가상환경 재활성화
deactivate
source venv/bin/activate
```

## 🎯 빠른 테스트 스크립트

```bash
#!/bin/bash
# quick_test.sh

echo "🔧 Starting Code-Monitor Test Suite..."

# Step 1: Docker
echo "\n1️⃣ Checking Docker..."
docker-compose up -d
sleep 5

# Step 2: Health Check
echo "\n2️⃣ Testing Health..."
curl -s http://localhost:8000/health | jq

# Step 3: Create User
echo "\n3️⃣ Creating Test User..."
USER_ID=$(curl -s -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@lab.com","role":"student"}' \
  | jq -r '.id')

echo "Created User ID: $USER_ID"

# Step 4: Create Submission
echo "\n4️⃣ Creating Weekly Submission..."
curl -s -X POST "http://localhost:8000/api/users/$USER_ID/submissions" \
  -H "Content-Type: application/json" \
  -d '{"week_start_date":"2025-10-13","code_lines_added":500,"documents_created":3}' \
  | jq

# Step 5: Check Rankings
echo "\n5️⃣ Checking Rankings..."
curl -s http://localhost:8000/api/rankings/current | jq

echo "\n✅ Test Suite Complete!"
```

## 📖 참고 문서

- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- README: [README_QUICKSTART.md](./README_QUICKSTART.md)
- System Design: [lab-knowledge-system-design.md](./lab-knowledge-system-design.md)
