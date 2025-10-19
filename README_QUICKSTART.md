# Code-Monitor Quick Start Guide

## 🚀 빠른 시작 (5분)

### 1. Docker 서비스 시작

```bash
# PostgreSQL + Redis 시작
docker-compose up -d

# 상태 확인
docker-compose ps
```

### 2. 가상환경 설정

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 데이터베이스 초기화

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

### 4. Backend API 시작

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**확인:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 5. Dashboard 시작

**새 터미널:**
```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**확인:**
- Dashboard: http://localhost:8501

---

## 📝 첫 사용자 추가

### Option A: Dashboard 사용
1. Dashboard → "➕ Add User" 페이지
2. 정보 입력
3. "Add Member" 클릭

### Option B: API 직접 호출
```bash
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "김철수",
    "email": "student1@lab.com",
    "github_username": "student1",
    "repo_url": "https://github.com/lab/student1",
    "role": "student"
  }'
```

### Option C: Python 스크립트
```python
import requests

response = requests.post(
    "http://localhost:8000/api/users",
    json={
        "name": "이영희",
        "email": "student2@lab.com",
        "github_username": "student2",
        "role": "student"
    }
)
print(response.json())
```

---

## ✅ 동작 확인

### 1. API Health Check
```bash
curl http://localhost:8000/health
```

**기대 응답:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. 사용자 목록 조회
```bash
curl http://localhost:8000/api/users
```

### 3. Dashboard 확인
- http://localhost:8501 접속
- "👥 Users" 페이지에서 추가한 사용자 확인

---

## 🛑 종료

```bash
# Backend API: Ctrl+C

# Dashboard: Ctrl+C

# Docker 서비스
docker-compose down

# (데이터 완전 삭제)
docker-compose down -v
```

---

## 🐛 문제 해결

### "Cannot connect to database"
```bash
# Docker 상태 확인
docker-compose ps

# PostgreSQL 로그 확인
docker-compose logs postgres

# 재시작
docker-compose restart postgres
```

### "Module not found"
```bash
# 가상환경 활성화 확인
which python  # venv 경로 확인

# 의존성 재설치
pip install -r requirements.txt
```

### "Address already in use"
```bash
# 포트 확인
lsof -i :8000  # API
lsof -i :8501  # Dashboard
lsof -i :5432  # PostgreSQL

# 프로세스 종료
kill -9 <PID>
```

---

## 📊 현재 MVP 기능

✅ **완료:**
- PostgreSQL + Redis Docker setup
- Database models (5 tables)
- Database initialization
- User CRUD API (GET, POST)
- Basic Streamlit dashboard
- Health check endpoint

⏳ **다음 Phase:**
- Git sync service
- Weekly submission API
- Rankings calculation
- Git metrics collection
- Advanced dashboard features

---

## 🔗 참고 문서

- [System Design](./lab-knowledge-system-design.md)
- [Workflow Guide](./docs/WORKFLOW.md)
- [Full README](./README.md)
