# 🎉 Code-Monitor 배포 성공 보고서

**배포 일시**: 2025-10-21 04:57 (KST)
**서버**: Connectome node3 (147.47.200.154)
**배포 방식**: Manual + Background processes

---

## ✅ 배포 완료 상태

### 📊 서비스 현황

| 서비스 | 상태 | 포트 | 프로세스 |
|--------|------|------|----------|
| **Backend (FastAPI)** | ✅ Running | 8000 | uvicorn (PID: 806058) |
| **Frontend (Next.js)** | ✅ Running | 3000 | next-server (PID: 806384) |
| **Database (SQLite)** | ✅ Ready | - | code_monitor.db |

### 🌐 접속 정보

**외부 접속 URL** (연구실 네트워크):
- Frontend: `http://node3.connectome:3000` 또는 `http://147.47.200.154:3000`
- Backend API: `http://node3.connectome:8000` 또는 `http://147.47.200.154:8000`
- API Documentation: `http://node3.connectome:8000/docs`

**서버 내부 접속**:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

---

## 🔧 배포 과정에서 해결한 문제들

### 1️⃣ PostgreSQL 권한 문제
**문제**: 일반 사용자(connectome1)에게 PostgreSQL superuser 권한 없음

**해결책**: SQLite로 대체
- Database URL: `sqlite:///./code_monitor.db`
- 위치: `~/code-monitor/backend/code_monitor.db`
- 장점: 권한 불필요, 파일 기반, 쉬운 백업
- 향후: PostgreSQL 마이그레이션 가능 (DATABASE_URL만 변경)

### 2️⃣ Pydantic Settings 호환성
**문제**: `.env` 파일의 extra fields가 Pydantic v2에서 거부됨

**해결책**: `backend/app/core/config.py` 수정
```python
class Config:
    env_file = ".env"
    case_sensitive = True
    extra = "ignore"  # 추가
```

### 3️⃣ Python 3.8 Union Type 문법
**문제**: Python 3.10+ 문법 `str | None`이 Python 3.8에서 미지원

**해결책**: `backend/app/api/users.py` 수정
```python
# Before
github_username: str | None = None

# After
from typing import Optional
github_username: Optional[str] = None
```

### 4️⃣ TypeScript 타입 에러 (Frontend)
**문제**: Recharts PieChart label prop 타입 불일치

**해결책**: `frontend/src/components/charts/ScoreBreakdownChart.tsx` 수정
```typescript
label={({ name, percent }: any) => `${name}: ${((percent as number) * 100).toFixed(0)}%`}
```

### 6️⃣ NextAuth UntrustedHost 에러
**문제**: IP 주소 접속 시 NextAuth가 UntrustedHost 에러 발생
```
UntrustedHost: Host must be trusted. URL was: http://147.47.200.154:3000
```

**해결책**: `frontend/src/auth.ts` 수정
```typescript
export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true, // Allow IP address access for deployment
  providers: [...]
})
```

### 5️⃣ Alembic 설정 누락
**문제**: `alembic.ini` 파일 없음, 마이그레이션 불가

**해결책**: `app.core.database.init_db()` 함수 사용
```python
python -c 'from app.core.database import init_db; init_db()'
```

---

## 📁 배포된 파일 구조

```
~/code-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── api/
│   │   ├── models/
│   │   └── services/
│   ├── venv/  (Python 가상환경)
│   ├── .env
│   ├── code_monitor.db  (SQLite 데이터베이스)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── node_modules/
│   ├── .next/  (빌드 파일)
│   ├── .env.local
│   └── package.json
├── deployment/
│   ├── backend.slurm
│   ├── frontend.slurm
│   └── setup_db.sh
└── logs/
    ├── backend-test.log
    └── frontend-manual.log
```

---

## ✅ 검증 결과

### Backend API 테스트
```bash
$ curl http://localhost:8000/health
{"status":"healthy","database":"connected"}

$ curl http://localhost:8000/
{"app":"Code-Monitor","version":"0.1.0","status":"running"}

$ curl http://localhost:8000/api/users
[]  # 정상 (사용자 없음)
```

### Frontend 테스트
```bash
$ curl http://localhost:3000 | grep title
<title>Code-Monitor - Developer Performance Dashboard</title>
```

### 프로세스 확인
```bash
$ ps aux | grep uvicorn
connectome1  806058  uvicorn app.main:app --host 0.0.0.0 --port 8000

$ ps aux | grep next
connectome1  806384  next-server

$ netstat -tlnp | grep -E ':(3000|8000)'
tcp   0.0.0.0:8000   LISTEN   806058/python3
tcp6  :::3000        LISTEN   806384/next-server
```

---

## 🎓 연구원 온보딩 가이드

### 1️⃣ 접속 방법
1. 웹 브라우저 열기 (Chrome, Firefox, Safari)
2. URL 입력: `http://node3.connectome:3000`
3. "Sign in with GitHub" 클릭
4. GitHub 로그인
5. 권한 승인 (처음 한 번만)

### 2️⃣ 주간 제출 방법
1. 상단 메뉴 "Weekly Submit" 클릭
2. GitHub Repository 연결 (처음 한 번만)
3. 자동 수집된 데이터 확인 (커밋 수, 코드 라인)
4. 수동 입력 (문서 페이지, 주간 노트)
5. "Submit" 클릭

### 3️⃣ 랭킹 확인
1. "Rankings" 탭 클릭
2. 이번 주 순위 확인
3. 내 통계 확인

---

## 📝 관리자 유지보수 가이드

### 일일 체크
```bash
# SSH 접속
ssh connectome

# 서비스 상태 확인
ps aux | grep -E '(uvicorn|next-server)' | grep -v grep

# 헬스체크
curl http://localhost:8000/health
curl http://localhost:3000 | head -5

# 로그 확인
tail -50 ~/code-monitor/logs/backend-test.log
tail -50 ~/code-monitor/logs/frontend-manual.log
```

### 서비스 재시작
```bash
# Backend 재시작
pkill -f 'uvicorn app.main:app'
cd ~/code-monitor/backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &

# Frontend 재시작
pkill -f 'npm start'
cd ~/code-monitor/frontend
nohup npm start > ../logs/frontend.log 2>&1 &
```

### 데이터베이스 백업
```bash
cd ~/code-monitor/backend
cp code_monitor.db code_monitor.db.backup.$(date +%Y%m%d)
```

---

## ⚠️ 알려진 제한사항

### 1. PostgreSQL 미사용
- **현재**: SQLite 사용 (단일 파일 데이터베이스)
- **영향**: 동시 접속자 많을 경우 성능 저하 가능
- **해결**: 향후 PostgreSQL 마이그레이션 (서버 관리자 권한 필요)

### 2. 백그라운드 프로세스 (SLURM 미사용)
- **현재**: `nohup`으로 백그라운드 실행
- **영향**: 서버 재부팅 시 수동 재시작 필요
- **해결**: SLURM 스크립트 수정 후 `sbatch` 사용

### 3. 디스크 공간
- **현재**: 278GB 사용 가능 (92% 사용 중)
- **영향**: 로그 파일 누적 시 공간 부족 가능
- **해결**: 정기적인 로그 정리 필요

---

## 🚀 향후 개선 사항

### 우선순위 높음
1. **PostgreSQL 마이그레이션**
   - 서버 관리자에게 데이터베이스 생성 요청
   - `DATABASE_URL` 변경 후 마이그레이션

2. **자동 재시작 설정**
   - SLURM 스크립트 수정 (로그 경로 등)
   - 또는 systemd 서비스 설정

3. **로그 로테이션**
   - 주간/월간 로그 압축 및 보관
   - 오래된 로그 자동 삭제

### 우선순위 중간
4. **모니터링 설정**
   - 서비스 다운 시 알림
   - 리소스 사용량 모니터링

5. **백업 자동화**
   - 데이터베이스 일일 백업
   - Cron 작업 등록

### 우선순위 낮음
6. **성능 최적화**
   - Backend 워커 수 조정
   - Frontend 빌드 최적화

7. **보안 강화**
   - HTTPS 설정 (Let's Encrypt)
   - 방화벽 규칙 설정

---

## 📞 문의 및 지원

### 기술 지원
- **관리자**: [이름]
- **이메일**: [이메일]
- **Slack**: #code-monitor

### 긴급 상황
- **서버 다운**: 즉시 관리자에게 연락
- **데이터 손실**: 백업 복구 절차 참조
- **보안 이슈**: 즉시 관리자에게 보고

---

## 📚 추가 문서

- **사용자 가이드**: `QUICK_START_LAB.md`
- **배포 가이드**: `DEPLOYMENT_GUIDE.md`
- **관리자 체크리스트**: `ADMIN_DEPLOYMENT_CHECKLIST.md`
- **문서 인덱스**: `DEPLOYMENT_INDEX.md`

---

## 🎉 배포 성공!

**축하합니다!** Code-Monitor 시스템이 Connectome 서버에 성공적으로 배포되었습니다.

### 현재 상태
- ✅ Backend API: Running on port 8000
- ✅ Frontend: Running on port 3000
- ✅ Database: SQLite ready
- ✅ GitHub OAuth: Configured

### 다음 단계
1. 연구원들에게 접속 URL 공지
2. 사용 가이드 전달 (`QUICK_START_LAB.md`)
3. 초기 사용자 등록 및 테스트
4. 주간 제출 프로세스 테스트

---

**배포 완료 일시**: 2025-10-21 04:57 KST
**배포 담당**: Claude Code 🤖
**서버**: Connectome node3 (147.47.200.154)
**버전**: v0.1.0 (MVP)

**Happy Coding! 🚀**
