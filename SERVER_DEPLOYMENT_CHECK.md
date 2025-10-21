# Connectome Server 배포 가능성 체크

**서버:** node3 (connectome)
**체크 일자:** 2025-10-19

---

## ✅ 서버 환경

| 항목 | 상태 | 버전/정보 |
|------|------|-----------|
| **운영체제** | ✅ | Ubuntu 20.04.6 LTS (Focal Fossa) |
| **아키텍처** | ✅ | x86_64 (64-bit) |
| **커널** | ✅ | Linux 5.4.0-216-generic |
| **호스트명** | ✅ | node3 |

---

## 🐳 Docker 환경

| 항목 | 상태 | 상세 정보 |
|------|------|----------|
| **Docker** | ✅ 실행 중 | Docker version 24.0.7 |
| **Docker 서비스** | ✅ Active | 2025-10-13부터 실행 중 (6일) |
| **Docker Compose** | ✅ 설치됨 | /snap/bin/docker-compose (v1) |
| **사용자 권한** | ✅ 있음 | docker 그룹 소속 |
| **Docker Compose v2** | ⚠️ 미지원 | v1 형식만 사용 가능 |

### Docker 명령어 작동 상태
```bash
✅ docker ps         # 작동 (권한 있음)
✅ docker-compose    # 설치됨
⚠️  docker compose   # v2 미지원 (v1 사용)
```

---

## 🖥️ 시스템 리소스

### 디스크 공간
```
총 용량: 3.5TB
사용 중: 3.1TB (92%)
여유 공간: 293GB
```

**⚠️ 주의사항:**
- 디스크 사용률 92%로 높음
- Code-Monitor는 약 1-2GB 필요 (데이터베이스, 로그 포함)
- **충분한 공간 있음** (293GB 여유)

### 포트 사용 현황
| 포트 | 상태 | 사용 중인 서비스 |
|------|------|------------------|
| **5432** | ⚠️ 사용 중 | PostgreSQL 16 (기존) |
| **6379** | ✅ 사용 가능 | - |
| **8000** | ✅ 사용 가능 | - |

---

## 🗄️ 데이터베이스 환경

### PostgreSQL 16 (이미 실행 중)
```
✅ PostgreSQL 16 실행 중
- 포트: 5432 (localhost)
- 프로세스: 6개 활성
- 실행 시작: 2025-10-13
```

**배포 옵션:**
1. **기존 PostgreSQL 사용** (추천)
   - Docker PostgreSQL 불필요
   - 포트 충돌 없음
   - 리소스 절약
   - 기존 DB에 새 데이터베이스 생성

2. **Docker PostgreSQL 사용**
   - 다른 포트 사용 (예: 5433)
   - docker-compose.yml 수정 필요

### Redis
```
❌ Redis 실행 중이지 않음
✅ 포트 6379 사용 가능
→ Docker Redis 사용 가능 (권장)
```

---

## 🐍 Python 환경

| 항목 | 버전 | 상태 |
|------|------|------|
| **Python** | 3.8.10 | ✅ 설치됨 |
| **pip** | 20.0.2 | ✅ 설치됨 |
| **최소 요구사항** | Python 3.8+ | ✅ 충족 |

**참고:** Code-Monitor는 Python 3.10으로 개발되었지만 3.8과 호환 가능

---

## 📊 배포 가능성 종합 평가

### ✅ 가능 (권장 방법)

**Option 1: 하이브리드 배포 (추천)**
```yaml
PostgreSQL: 기존 서버 PostgreSQL 16 사용
Redis: Docker 컨테이너
Backend API: Python 직접 실행 또는 Docker
```

**장점:**
- 포트 충돌 없음
- 리소스 효율적
- 기존 인프라 활용
- 빠른 배포 가능

**필요한 작업:**
1. 기존 PostgreSQL에 `code_monitor` 데이터베이스 생성
2. Redis만 Docker로 실행
3. Backend API 배포
4. 설정 파일 수정 (DATABASE_URL)

---

### ⚠️ 가능하지만 주의 필요

**Option 2: 완전 Docker 배포**
```yaml
PostgreSQL: Docker (포트 5433)
Redis: Docker (포트 6379)
Backend API: Docker
```

**장점:**
- 격리된 환경
- 쉬운 관리

**단점:**
- 포트 변경 필요 (5432 → 5433)
- 추가 리소스 사용
- 기존 PostgreSQL과 중복

---

## 🚀 배포 가이드 (Option 1 추천)

### 1단계: 기존 PostgreSQL에 DB 생성
```bash
ssh server
sudo -u postgres psql
CREATE DATABASE code_monitor;
CREATE USER lab WITH PASSWORD 'lab123';
GRANT ALL PRIVILEGES ON DATABASE code_monitor TO lab;
\q
```

### 2단계: docker-compose.yml 수정
```yaml
# Redis만 실행
services:
  redis:
    image: redis:7-alpine
    container_name: code-monitor-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

### 3단계: 설정 파일 수정
```python
# backend/app/core/config.py
DATABASE_URL: str = "postgresql://lab:lab123@localhost:5432/code_monitor"
REDIS_URL: str = "redis://localhost:6379/0"
```

### 4단계: 배포 실행
```bash
# 서버에 코드 복사
scp -r /Users/jiookcha/Documents/git/Code-Monitor server:/home/connectome/

# 서버에서 실행
ssh server
cd /home/connectome/Code-Monitor

# Redis 시작
docker-compose up -d redis

# Python 의존성 설치
cd backend
pip3 install --user -r requirements.txt

# 데이터베이스 초기화
cd ..
python3 scripts/init_db.py

# API 시작
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🔐 보안 고려사항

1. **방화벽 설정**
   - 포트 8000 외부 접근 제한 확인
   - 필요시 nginx 리버스 프록시 사용

2. **데이터베이스 접근**
   - PostgreSQL은 localhost만 접근 허용 (현재 설정)
   - 외부 접근 차단됨 (안전)

3. **환경 변수**
   - 민감한 정보는 .env 파일로 관리
   - 비밀번호 변경 권장

---

## 📝 예상 문제 및 해결책

### 문제 1: pip 버전이 낮음 (20.0.2)
```bash
python3 -m pip install --user --upgrade pip
```

### 문제 2: Python 3.8 호환성
```bash
# requirements.txt 일부 수정 필요할 수 있음
# 테스트 후 확인
```

### 문제 3: docker-compose 권한 에러
```bash
# snap 경로 문제
# docker-compose 대신 /snap/bin/docker-compose 전체 경로 사용
/snap/bin/docker-compose up -d redis
```

---

## ✅ 최종 결론

**배포 가능 여부:** ✅ **가능**

**권장 배포 방식:**
- 기존 PostgreSQL 16 활용
- Redis만 Docker로 실행
- Backend API Python 직접 실행

**예상 소요 시간:** 30-60분

**디스크 사용:** 약 1-2GB (충분한 여유 공간)

**성능:** 서버 사양 충분, 안정적 운영 가능

---

## 📞 다음 단계

1. ✅ 서버 환경 체크 완료
2. ⏳ 배포 방식 결정 (Option 1 or 2)
3. ⏳ 설정 파일 수정
4. ⏳ 서버에 코드 배포
5. ⏳ 테스트 및 검증

**준비 완료!** 배포를 진행하시겠습니까?
