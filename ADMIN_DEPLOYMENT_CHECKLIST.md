# 🔧 관리자용 배포 체크리스트

**Code-Monitor 시스템 배포 완전 가이드**

---

## 📋 배포 단계별 체크리스트

### ✅ Phase 1: 준비 단계 (로컬에서 실행)

- [ ] **1.1 Git 상태 확인**
  ```bash
  cd /Users/jiookcha/Documents/git/Code-Monitor
  git status  # clean 상태 확인
  ```

- [ ] **1.2 배포 전 체크 실행**
  ```bash
  ./deployment/pre-deploy-check.sh
  ```
  모든 항목이 ✓ 통과해야 함

- [ ] **1.3 환경 변수 확인**
  - `backend/.env` 파일 존재
  - `frontend/.env.local` 파일 존재
  - 민감한 정보(API 키, 비밀번호) 확인

### ✅ Phase 2: GitHub OAuth 앱 생성

- [ ] **2.1 GitHub 접속**
  - https://github.com/settings/developers 접속

- [ ] **2.2 새 OAuth App 생성**
  - **Application name**: `Code-Monitor (Lab)`
  - **Homepage URL**: `http://node3.connectome:3000`
  - **Callback URL**: `http://node3.connectome:3000/api/auth/callback/github`
  - **Register application** 클릭

- [ ] **2.3 Client ID/Secret 복사**
  - Client ID 복사 → 메모장에 임시 저장
  - Generate new client secret 클릭
  - Client Secret 복사 → 메모장에 임시 저장
  - ⚠️ **중요**: Secret은 한 번만 표시됨!

- [ ] **2.4 Frontend .env.local 업데이트**
  ```bash
  # frontend/.env.local 파일 열기
  nano frontend/.env.local

  # GITHUB_CLIENT_ID와 GITHUB_CLIENT_SECRET 값 붙여넣기
  GITHUB_CLIENT_ID=Ov23li...
  GITHUB_CLIENT_SECRET=...
  ```

### ✅ Phase 3: 서버로 파일 전송

- [ ] **3.1 배포 스크립트 실행**
  ```bash
  cd /Users/jiookcha/Documents/git/Code-Monitor
  ./deployment/deploy.sh
  ```

- [ ] **3.2 전송 완료 확인**
  - Backend 파일 전송 완료 메시지
  - Frontend 파일 전송 완료 메시지
  - Deployment 스크립트 전송 완료 메시지

### ✅ Phase 4: 서버 설정 (Connectome에서 실행)

- [ ] **4.1 서버 SSH 접속**
  ```bash
  ssh connectome
  ```

- [ ] **4.2 프로젝트 디렉토리 확인**
  ```bash
  cd ~/code-monitor
  ls -la  # backend, frontend, deployment 폴더 확인
  ```

- [ ] **4.3 PostgreSQL 데이터베이스 설정**
  ```bash
  cd deployment
  chmod +x setup_db.sh
  ./setup_db.sh
  ```

  **예상 출력:**
  ```
  [1/4] PostgreSQL 서비스 확인...
  ✓ PostgreSQL is active
  [2/4] 데이터베이스 및 사용자 생성...
  ✓ Database created
  [3/4] Backend 가상환경 설정...
  ✓ Virtual environment created
  [4/4] Alembic 마이그레이션 실행...
  ✓ Database schema created
  ```

- [ ] **4.4 데이터베이스 연결 테스트**
  ```bash
  psql -h localhost -U codemonitor -d codemonitor
  # 비밀번호: codemonitor_secure_2025

  # PostgreSQL 프롬프트에서:
  \dt  # 테이블 목록 확인 (users, rankings 등)
  \q   # 종료
  ```

- [ ] **4.5 Frontend 환경 변수 수정 (서버 호스트명 확인)**
  ```bash
  # 현재 노드 확인
  hostname  # 예: node3

  # frontend/.env.local 수정
  cd ~/code-monitor/frontend
  nano .env.local

  # 호스트명에 맞게 URL 수정
  NEXTAUTH_URL=http://node3.connectome:3000
  NEXT_PUBLIC_API_URL=http://node3.connectome:8000
  ```

- [ ] **4.6 Backend Python 패키지 설치**
  ```bash
  cd ~/code-monitor/backend
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  deactivate
  ```

- [ ] **4.7 Frontend Node.js 패키지 설치**
  ```bash
  cd ~/code-monitor/frontend
  npm install
  npm run build
  ```

### ✅ Phase 5: SLURM 작업 제출

- [ ] **5.1 로그 디렉토리 생성**
  ```bash
  mkdir -p ~/code-monitor/logs
  ```

- [ ] **5.2 Backend 서비스 시작**
  ```bash
  cd ~/code-monitor/deployment
  sbatch backend.slurm
  ```

  **성공 메시지:**
  ```
  Submitted batch job 12345
  ```

- [ ] **5.3 Backend 로그 확인 (30초 대기)**
  ```bash
  sleep 30
  tail -n 50 ~/code-monitor/logs/backend.log
  ```

  **예상 로그 (정상):**
  ```
  INFO:     Started server process [PID]
  INFO:     Uvicorn running on http://0.0.0.0:8000
  INFO:     Application startup complete
  ```

- [ ] **5.4 Backend 헬스체크**
  ```bash
  curl http://localhost:8000/health
  ```

  **예상 응답:**
  ```json
  {"status":"healthy"}
  ```

- [ ] **5.5 Frontend 서비스 시작**
  ```bash
  cd ~/code-monitor/deployment
  sbatch frontend.slurm
  ```

- [ ] **5.6 Frontend 로그 확인 (30초 대기)**
  ```bash
  sleep 30
  tail -n 50 ~/code-monitor/logs/frontend.log
  ```

  **예상 로그 (정상):**
  ```
  ready - started server on 0.0.0.0:3000
  ```

### ✅ Phase 6: 배포 검증

- [ ] **6.1 SLURM 작업 상태 확인**
  ```bash
  squeue -u $USER
  ```

  **두 개 작업이 R(Running) 상태여야 함:**
  ```
  JOBID   NAME                    ST  TIME
  12345   code-monitor-backend    R   0:05
  12346   code-monitor-frontend   R   0:02
  ```

- [ ] **6.2 포트 사용 확인**
  ```bash
  lsof -i :8000  # Backend
  lsof -i :3000  # Frontend
  ```

- [ ] **6.3 웹 브라우저 테스트**
  - [ ] Frontend 접속: http://node3.connectome:3000
  - [ ] 로그인 화면 표시 확인
  - [ ] "Sign in with GitHub" 버튼 확인

- [ ] **6.4 GitHub OAuth 테스트**
  - [ ] "Sign in with GitHub" 클릭
  - [ ] GitHub 로그인 페이지로 리다이렉트
  - [ ] 로그인 후 대시보드로 리다이렉트
  - [ ] 상단에 프로필 사진/이름 표시

- [ ] **6.5 API 엔드포인트 테스트**
  ```bash
  # 사용자 목록 조회
  curl http://localhost:8000/api/users

  # 랭킹 조회
  curl http://localhost:8000/api/rankings
  ```

### ✅ Phase 7: 연구원 온보딩 준비

- [ ] **7.1 사용자 가이드 공유**
  - [ ] `QUICK_START_LAB.md` 파일 연구원들에게 전달
  - [ ] 접속 URL 공지: `http://node3.connectome:3000`

- [ ] **7.2 슬랙/이메일 공지**
  ```
  제목: 🚀 Code-Monitor 시스템 오픈!

  안녕하세요,

  연구실 생산성 모니터링 시스템 Code-Monitor가 오픈되었습니다.

  📌 접속 URL: http://node3.connectome:3000
  📌 로그인: GitHub 계정으로 로그인
  📌 사용법: 첨부된 QUICK_START_LAB.md 참조

  매주 일요일까지 주간 제출 부탁드립니다!

  문의사항: [관리자 이메일/슬랙]
  ```

- [ ] **7.3 테스트 계정으로 전체 플로우 테스트**
  - [ ] 로그인
  - [ ] Repository 연결
  - [ ] 주간 제출
  - [ ] 랭킹 확인
  - [ ] 로그아웃

---

## 🔧 유지보수 체크리스트

### 일일 체크 (자동화 권장)

- [ ] SLURM 작업 상태 확인
  ```bash
  squeue -u $USER
  ```

- [ ] 서비스 헬스체크
  ```bash
  curl http://localhost:8000/health
  curl http://localhost:3000
  ```

- [ ] 로그 파일 확인 (에러 검색)
  ```bash
  grep -i error ~/code-monitor/logs/*.log
  ```

### 주간 체크

- [ ] 데이터베이스 백업
  ```bash
  cd ~/code-monitor/deployment
  ./backup_db.sh
  ```

- [ ] 디스크 공간 확인
  ```bash
  df -h ~/code-monitor
  ```

- [ ] 랭킹 데이터 검증
  - 이번 주 제출 건수 확인
  - 비정상적인 점수 확인

### 월간 체크

- [ ] PostgreSQL 성능 최적화
  ```sql
  VACUUM ANALYZE;
  REINDEX DATABASE codemonitor;
  ```

- [ ] 로그 파일 로테이션
  ```bash
  cd ~/code-monitor/logs
  gzip backend-*.log.1
  gzip frontend-*.log.1
  ```

- [ ] 시스템 업데이트 확인
  - Backend 패키지 업데이트
  - Frontend 패키지 업데이트
  - 보안 패치 적용

---

## 🚨 트러블슈팅

### 문제 1: Backend 서비스가 시작되지 않음

**진단:**
```bash
tail -100 ~/code-monitor/logs/backend.log
```

**일반적인 원인:**
- 데이터베이스 연결 실패 → `.env`의 DATABASE_URL 확인
- 포트 충돌 → `lsof -i :8000`로 확인 후 프로세스 종료
- Python 패키지 누락 → `pip install -r requirements.txt` 재실행

### 문제 2: Frontend 빌드 실패

**진단:**
```bash
cd ~/code-monitor/frontend
npm run build
```

**일반적인 원인:**
- Node.js 버전 불일치 → `node -v` (v18+ 필요)
- 환경 변수 누락 → `.env.local` 파일 확인
- 메모리 부족 → SLURM 작업 메모리 증가

### 문제 3: GitHub OAuth 실패

**진단:**
- GitHub OAuth 앱 설정 확인
- Callback URL 정확성 확인

**해결:**
1. GitHub Developer Settings 재확인
2. `.env.local`의 GITHUB_CLIENT_ID/SECRET 재확인
3. Frontend 서비스 재시작

### 문제 4: 데이터베이스 연결 실패

**진단:**
```bash
psql -h localhost -U codemonitor -d codemonitor
```

**해결:**
1. PostgreSQL 서비스 상태 확인
2. 비밀번호 확인
3. `.env`의 DATABASE_URL 확인

---

## 📞 지원 연락처

- **시스템 관리자**: [이름] ([이메일])
- **기술 지원**: [Slack 채널]
- **긴급 연락**: [전화번호]

---

## 📚 참고 문서

1. **DEPLOYMENT_GUIDE.md** - 전체 배포 가이드 (관리자 + 연구원)
2. **QUICK_START_LAB.md** - 연구원용 빠른 시작 가이드
3. **DEPLOY_CONNECTOME.md** - Connectome 서버 배포 상세 문서
4. **README.md** - 프로젝트 전체 개요

---

**마지막 업데이트**: 2025-10-21
**버전**: 1.0
**배포 상태**: Production Ready ✅
