# Code-Monitor 배포 및 사용 가이드

**연구실 생산성 모니터링 시스템**

---

## 📋 목차

1. [관리자용 - 서버 배포 가이드](#1-관리자용---서버-배포-가이드)
2. [연구원용 - GitHub OAuth 설정](#2-연구원용---github-oauth-설정)
3. [연구원용 - 시스템 사용법](#3-연구원용---시스템-사용법)
4. [문제 해결 FAQ](#4-문제-해결-faq)

---

## 1. 관리자용 - 서버 배포 가이드

### 📌 사전 준비사항

- [ ] Connectome 서버 접속 권한
- [ ] GitHub 계정 (OAuth 앱 생성용)
- [ ] PostgreSQL 관리자 권한

### 🚀 Step 1: 서버로 파일 전송

```bash
# 로컬 머신에서 실행
cd /Users/jiookcha/Documents/git/Code-Monitor

# 배포 스크립트 실행
./deployment/deploy.sh
```

**스크립트가 자동으로 수행하는 작업:**
- ✅ Connectome 서버에 프로젝트 디렉토리 생성
- ✅ Backend 파일 전송 (Python 파일, requirements)
- ✅ Frontend 파일 전송 (Next.js 프로젝트)
- ✅ 배포 스크립트 전송 (SLURM 작업 파일)

### 🚀 Step 2: 서버 SSH 접속 및 환경 설정

```bash
# Connectome 서버 접속
ssh connectome

# 프로젝트 디렉토리로 이동
cd ~/code-monitor
```

### 🚀 Step 3: PostgreSQL 데이터베이스 설정

```bash
# 데이터베이스 초기화 스크립트 실행
cd deployment
chmod +x setup_db.sh
./setup_db.sh
```

**스크립트가 자동으로 수행하는 작업:**
1. PostgreSQL에 `codemonitor` 데이터베이스 생성
2. `codemonitor` 사용자 생성 (비밀번호: secure-password-here)
3. 권한 설정
4. 데이터베이스 테이블 생성 (Alembic 마이그레이션)

**✅ 성공 확인:**
```bash
psql -h localhost -U codemonitor -d codemonitor
# 비밀번호 입력: secure-password-here
# PostgreSQL 프롬프트가 나타나면 성공
\dt  # 테이블 목록 확인
\q   # 종료
```

### 🚀 Step 4: 환경 변수 설정

**Backend 환경 변수 (.env):**
```bash
cd ~/code-monitor/backend
nano .env
```

다음 내용 입력:
```bash
# Database
DATABASE_URL=postgresql://codemonitor:secure-password-here@localhost:5432/codemonitor

# Security
SECRET_KEY=your-random-secret-key-minimum-32-characters-long

# CORS (프론트엔드 접근 허용)
CORS_ORIGINS=["http://node3.connectome:3000"]

# API Keys (선택사항 - LLM 기능용)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Frontend 환경 변수 (.env.local):**
```bash
cd ~/code-monitor/frontend
nano .env.local
```

다음 내용 입력:
```bash
# NextAuth
NEXTAUTH_URL=http://node3.connectome:3000
NEXTAUTH_SECRET=your-nextauth-random-secret-32-chars

# GitHub OAuth (Step 5에서 받은 값 입력)
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=...

# API URL
NEXT_PUBLIC_API_URL=http://node3.connectome:8000
```

### 🚀 Step 5: GitHub OAuth 앱 생성 (관리자)

1. **GitHub 접속**: https://github.com/settings/developers
2. **OAuth Apps 클릭** → **New OAuth App**

   **입력 정보:**
   - **Application name**: `Code-Monitor (Lab)`
   - **Homepage URL**: `http://node3.connectome:3000`
   - **Authorization callback URL**: `http://node3.connectome:3000/api/auth/callback/github`
   - **Description**: `Lab productivity monitoring system`

3. **Register application 클릭**

4. **Client ID 복사** → frontend `.env.local`에 붙여넣기

5. **Generate a new client secret 클릭**
   - **Client Secret 복사** → frontend `.env.local`에 붙여넣기
   - ⚠️ **중요**: Secret은 한 번만 표시됩니다. 안전하게 보관하세요!

6. **저장 확인**
   ```bash
   cd ~/code-monitor/frontend
   cat .env.local  # GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET 확인
   ```

### 🚀 Step 6: Python 가상환경 및 패키지 설치

```bash
# Backend 설정
cd ~/code-monitor/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 데이터베이스 마이그레이션 실행
alembic upgrade head

# 가상환경 비활성화
deactivate
```

### 🚀 Step 7: Node.js 패키지 설치

```bash
# Frontend 설정
cd ~/code-monitor/frontend
npm install

# Production 빌드 생성
npm run build
```

### 🚀 Step 8: SLURM 작업 제출

```bash
# 로그 디렉토리 생성
mkdir -p ~/code-monitor/logs

# Backend 서비스 시작
cd ~/code-monitor/deployment
sbatch backend.slurm

# Frontend 서비스 시작 (Backend 시작 후 30초 대기)
sleep 30
sbatch frontend.slurm
```

**작업 상태 확인:**
```bash
# SLURM 작업 상태
squeue -u $USER

# 출력 예시:
# JOBID   PARTITION   NAME                    USER    ST  TIME
# 12345   main        code-monitor-backend    user    R   0:05
# 12346   main        code-monitor-frontend   user    R   0:02
```

**로그 확인:**
```bash
# Backend 로그
tail -f ~/code-monitor/logs/backend.log

# Frontend 로그
tail -f ~/code-monitor/logs/frontend.log
```

### 🚀 Step 9: 서비스 동작 확인

```bash
# Backend API 헬스체크
curl http://localhost:8000/health
# 예상 출력: {"status":"healthy"}

# Frontend 접속 확인
curl http://localhost:3000
# 예상 출력: HTML 페이지
```

**웹 브라우저에서 확인:**
- Frontend: http://node3.connectome:3000
- Backend API Docs: http://node3.connectome:8000/docs

### ✅ 배포 완료!

연구원들에게 다음 정보를 공유하세요:
- **접속 URL**: http://node3.connectome:3000
- **로그인 방법**: GitHub 계정으로 로그인
- **사용 가이드**: 아래 "연구원용 - 시스템 사용법" 섹션 참조

---

## 2. 연구원용 - GitHub OAuth 설정

### 📌 사전 준비사항

- [ ] GitHub 계정 (개인 또는 연구실 계정)
- [ ] 연구실 Connectome 서버 접근 권한

### 🔑 Step 1: 시스템 접속

1. **웹 브라우저 열기**
   - Chrome, Firefox, Safari 등 사용

2. **URL 입력**
   ```
   http://node3.connectome:3000
   ```

3. **로그인 화면 확인**
   - "Sign in with GitHub" 버튼이 보여야 합니다

### 🔑 Step 2: GitHub 로그인

1. **"Sign in with GitHub" 클릭**

2. **GitHub 로그인 페이지**
   - GitHub 아이디/비밀번호 입력
   - 2FA 설정되어 있으면 인증 코드 입력

3. **권한 승인 (처음 한 번만)**
   - "Authorize Code-Monitor" 화면이 나타남
   - 요청 권한:
     - ✅ Read access to your profile (이름, 이메일)
     - ✅ Read access to your repositories (코드 분석용)
   - **"Authorize" 버튼 클릭**

4. **대시보드 리다이렉트**
   - 로그인 성공 시 자동으로 대시보드로 이동
   - 상단에 GitHub 프로필 사진/이름 표시

### 🔑 Step 3: 프로필 확인

1. **우측 상단 프로필 아이콘 클릭**
2. **내 정보 확인**
   - GitHub 사용자명
   - 이메일
   - 가입일

---

## 3. 연구원용 - 시스템 사용법

### 📊 대시보드 둘러보기

**메인 화면 구성:**
- **주간 랭킹**: 이번 주 연구원별 생산성 순위
- **내 통계**: 나의 코드 라인 수, 커밋 수, 문서 작성량
- **팀 통계**: 연구실 전체 생산성 트렌드

### ✍️ 주간 제출하기 (매주 1회)

**Step 1: 제출 페이지 이동**
1. 상단 메뉴에서 **"Weekly Submit"** 클릭
2. 이번 주 날짜 확인 (예: 2025-10-13 ~ 2025-10-19)

**Step 2: GitHub Repository 연동 (처음 한 번만)**
1. **"Add Repository" 버튼 클릭**
2. **Repository 정보 입력**
   - Repository URL: `https://github.com/username/repo-name`
   - 설명: `논문 실험 코드`, `데이터 분석 프로젝트` 등
3. **"Connect" 버튼 클릭**
4. 연동된 Repository 목록 확인

**Step 3: 자동 수집된 데이터 확인**
시스템이 자동으로 수집한 데이터:
- ✅ **커밋 수**: 이번 주 Git 커밋 개수
- ✅ **코드 라인 수**: 추가된 코드 라인 (삭제된 라인 제외)
- ✅ **파일 수정 개수**: 변경된 파일 수

**Step 4: 수동 입력 데이터 추가**
자동 수집되지 않는 데이터 직접 입력:
- **문서 작성**: 논문, 보고서 페이지 수
- **주간 노트**: 이번 주 주요 성과/배운 점 간단히 작성

  예시:
  ```
  - BERT 모델 fine-tuning 완료 (accuracy 92%)
  - 데이터 전처리 파이프라인 최적화 (2배 속도 향상)
  - 논문 Introduction 섹션 작성 (3페이지)
  ```

**Step 5: 제출**
1. 모든 정보 확인
2. **"Submit Weekly Report" 버튼 클릭**
3. 제출 완료 메시지 확인

### 📈 랭킹 시스템 이해하기

**점수 계산 방식:**
```
총점 = (커밋 수 × 5) + (코드 라인 수 × 0.1) + (문서 페이지 × 10)
```

**예시:**
- 커밋 20개 = 100점
- 코드 500줄 = 50점
- 문서 5페이지 = 50점
- **총 200점**

**랭킹 확인:**
1. **"Rankings" 탭 클릭**
2. **이번 주 랭킹 확인**
   - 1위부터 순위 표시
   - 내 순위 강조 표시
3. **월간/연간 랭킹**
   - 기간 선택하여 장기 트렌드 확인

### 🔍 코드 검색 기능 (RAG)

**다른 연구원 코드 찾기:**

1. **"Code Explorer" 탭 클릭**

2. **자연어로 질문 입력**

   예시 질문:
   - "데이터 전처리 파이프라인 코드 있어?"
   - "효율적인 정렬 알고리즘 구현 예시는?"
   - "Transformer 모델 누가 구현했어?"

3. **검색 결과 확인**
   - 관련 코드 스니펫 표시
   - 작성자 이름 표시
   - 파일 경로 표시

4. **상세 코드 보기**
   - 코드 클릭 → 전체 파일 내용 확인
   - "Ask Follow-up" → 추가 질문 가능

---

## 4. 문제 해결 FAQ

### ❓ Q1: GitHub 로그인이 안 돼요

**증상:**
- "Sign in with GitHub" 클릭 후 에러 페이지
- "Invalid OAuth callback URL" 에러

**해결 방법:**
1. **관리자에게 문의**
   - GitHub OAuth 설정 확인 요청
   - Callback URL이 올바른지 확인

2. **브라우저 캐시 삭제**
   ```
   Chrome: 설정 → 개인정보 및 보안 → 인터넷 사용 기록 삭제
   ```

3. **다른 브라우저 시도**
   - Chrome, Firefox, Safari 등

### ❓ Q2: Repository 연동이 안 돼요

**증상:**
- "Failed to fetch repository data"
- "Invalid repository URL"

**해결 방법:**
1. **Repository URL 확인**
   - 올바른 형식: `https://github.com/username/repo-name`
   - Private repository는 권한 필요

2. **GitHub Personal Access Token 생성 (Private repo인 경우)**
   ```
   GitHub Settings → Developer settings → Personal access tokens
   → Generate new token → repo 권한 선택 → 토큰 복사
   ```

3. **토큰 입력**
   - 시스템 설정에서 "GitHub Token" 입력 필드에 붙여넣기

### ❓ Q3: 데이터가 자동 수집이 안 돼요

**증상:**
- 커밋 수가 0으로 표시
- 코드 라인 수가 업데이트 안 됨

**해결 방법:**
1. **Repository 연동 확인**
   - "Settings" → "Connected Repositories" 확인
   - Repository가 활성화되어 있는지 확인

2. **Git 커밋 날짜 확인**
   - 시스템은 "이번 주" 커밋만 집계
   - 주간 제출 기간 (월요일 ~ 일요일) 확인

3. **수동 동기화 실행**
   - "Weekly Submit" 페이지에서 "Sync Now" 버튼 클릭

### ❓ Q4: 페이지가 느려요

**해결 방법:**
1. **브라우저 캐시 삭제**
2. **활성 탭 개수 줄이기**
3. **관리자에게 서버 상태 확인 요청**

### ❓ Q5: 제출했는데 랭킹에 반영이 안 돼요

**원인:**
- 시스템은 매시간 랭킹 업데이트 (0분, 30분)

**해결 방법:**
1. **30분 대기 후 새로고침**
2. **"Rankings" 탭에서 "Refresh" 버튼 클릭**
3. **그래도 안 되면 관리자에게 문의**

### ❓ Q6: 다른 사람 코드가 검색이 안 돼요

**원인:**
- RAG 시스템은 제출된 코드만 인덱싱
- 개인 설정에서 "코드 공유" 비활성화된 경우

**해결 방법:**
1. **코드 공유 설정 확인**
   - "Settings" → "Privacy" → "Share my code in search" 활성화 확인
2. **관리자에게 RAG 인덱싱 상태 확인 요청**

---

## 📞 지원 및 문의

### 기술 지원
- **담당자**: [관리자 이름]
- **이메일**: [관리자 이메일]
- **Slack**: #code-monitor

### 긴급 문의
- **서버 다운**: 즉시 관리자에게 연락
- **데이터 손실**: 백업 복구 요청

### 기능 제안
- **새로운 기능 아이디어**: GitHub Issues 등록
- **UI/UX 개선 제안**: 설문조사 참여

---

## 📚 추가 자료

- **시스템 설계 문서**: `lab-knowledge-system-design.md`
- **API 문서**: http://node3.connectome:8000/docs
- **GitHub Repository**: [링크]

---

**Last Updated**: 2025-10-21
**Version**: 1.0
**Maintained by**: Claude Code 🤖
