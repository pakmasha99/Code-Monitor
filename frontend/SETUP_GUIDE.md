# Code-Monitor Frontend Setup Guide

## 🚀 Quick Start (5분 안에 완료)

### 1. GitHub OAuth App 생성

#### Step 1: GitHub 설정 페이지로 이동
1. GitHub에 로그인
2. 우측 상단 프로필 → **Settings** 클릭
3. 좌측 메뉴 맨 아래 **Developer settings** 클릭
4. 좌측 메뉴에서 **OAuth Apps** 클릭
5. **New OAuth App** 버튼 클릭

#### Step 2: OAuth App 정보 입력
```
Application name:        Code-Monitor
Homepage URL:            http://localhost:3001
Application description: Developer Performance Dashboard (선택사항)
Authorization callback URL: http://localhost:3001/api/auth/callback/github
```

⚠️ **중요:** Authorization callback URL을 정확히 입력하세요!

#### Step 3: Client ID & Secret 복사
1. **Register application** 버튼 클릭
2. **Client ID** 복사 (나중에 사용)
3. **Generate a new client secret** 버튼 클릭
4. 생성된 **Client Secret** 즉시 복사 (다시 볼 수 없음!)

---

### 2. 환경 변수 설정

#### Step 1: .env.local 파일 생성
```bash
cd frontend
cp .env.local.example .env.local
```

#### Step 2: .env.local 파일 편집
```bash
# NextAuth.js Configuration
NEXTAUTH_URL=http://localhost:3001
NEXTAUTH_SECRET=생성할_비밀키

# GitHub OAuth (위에서 복사한 값 입력)
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# FastAPI Backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Step 3: NEXTAUTH_SECRET 생성
터미널에서 실행:
```bash
openssl rand -base64 32
```

생성된 문자열을 `NEXTAUTH_SECRET`에 붙여넣기

---

### 3. FastAPI CORS 설정

Backend에서 프론트엔드 요청을 허용하도록 CORS 설정이 필요합니다.

#### backend/app/main.py 수정
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 4. 서버 실행

#### Terminal 1: Backend (FastAPI)
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Frontend (Next.js)
```bash
cd frontend
npm run dev
```

---

### 5. 테스트

1. 브라우저에서 http://localhost:3001 접속
2. **"Sign in with GitHub"** 버튼 클릭
3. GitHub 권한 승인
4. 자동으로 대시보드로 리다이렉트 ✅

---

## 📸 예상 화면

### 홈페이지 (로그인 전)
```
┌──────────────────────────────────────────┐
│      🎯 Code-Monitor                     │
│  Developer Performance Dashboard         │
│                                          │
│  [🐙 Sign in with GitHub]               │
└──────────────────────────────────────────┘
```

### 대시보드 (로그인 후)
```
┌──────────────────────────────────────────┐
│  🎯 Code-Monitor | Dashboard             │
│                           [Logout]       │
├──────────────────────────────────────────┤
│  Welcome back, 김철수! 👋                │
│                                          │
│  📊 Rank: #2   ⚡ Score: 80              │
│  💻 Lines: 850  🔥 Commits: 15          │
│                                          │
│  🏆 Current Week Leaderboard             │
│  🥇 이영희  130 points                   │
│  🥈 김철수  80 points (You)              │
│  🥉 박민수  65 points                    │
└──────────────────────────────────────────┘
```

---

## 🐛 트러블슈팅

### 문제 1: "Invalid Client ID"
- GitHub OAuth App의 Client ID가 정확한지 확인
- .env.local 파일이 frontend 디렉토리에 있는지 확인

### 문제 2: "Redirect URI Mismatch"
- GitHub OAuth App의 callback URL 확인:
  `http://localhost:3001/api/auth/callback/github`
- 포트 번호 확인 (3001)

### 문제 3: CORS 에러
- FastAPI backend에 CORS 미들웨어 추가 확인
- Backend가 실행 중인지 확인 (http://localhost:8000)

### 문제 4: "Failed to register user"
- FastAPI backend가 실행 중인지 확인
- PostgreSQL이 실행 중인지 확인
- Backend 로그 확인

---

## 🔒 보안 주의사항

### .env.local 파일
- **절대로 Git에 커밋하지 마세요!**
- `.gitignore`에 `.env.local` 추가됨

### Client Secret
- GitHub Client Secret은 한 번만 표시됨
- 분실 시 새로 생성 필요

### Production 배포 시
- `NEXTAUTH_URL`을 실제 도메인으로 변경
- GitHub OAuth App에 production callback URL 추가
- 강력한 `NEXTAUTH_SECRET` 사용

---

## ✅ 체크리스트

프론트엔드 설정 완료 확인:

- [ ] GitHub OAuth App 생성
- [ ] Client ID & Secret 복사
- [ ] `.env.local` 파일 생성 및 설정
- [ ] `NEXTAUTH_SECRET` 생성
- [ ] FastAPI CORS 설정
- [ ] Backend 서버 실행 (port 8000)
- [ ] Frontend 서버 실행 (port 3001)
- [ ] 로그인 테스트 성공
- [ ] 대시보드 접근 성공

---

## 📚 다음 단계

1. ✅ 리더보드 실시간 데이터 연동
2. ✅ Recharts 차트 추가
3. ✅ 사용자 프로필 페이지
4. ✅ 주간 활동 히트맵

---

**문제가 있나요?**
위 트러블슈팅 섹션을 참고하거나, Backend 로그를 확인해보세요!
