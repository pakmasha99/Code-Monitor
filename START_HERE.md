# 🚀 Code-Monitor 배포 시작 가이드

**역할에 맞는 문서를 선택하세요**

---

## 👤 당신은 누구인가요?

### 🔧 관리자 (시스템 배포 담당)

**지금 바로 시작 →** [ADMIN_DEPLOYMENT_CHECKLIST.md](ADMIN_DEPLOYMENT_CHECKLIST.md)

**준비물:**
- ✅ Connectome 서버 접속 권한
- ✅ GitHub 계정 (OAuth 앱 생성용)
- ✅ PostgreSQL 관리자 권한
- ✅ 30-60분 시간

**배포 단계 요약:**
1. 배포 전 체크 실행
2. GitHub OAuth 앱 생성
3. 서버로 파일 전송
4. PostgreSQL 데이터베이스 설정
5. SLURM 작업 제출
6. 배포 검증
7. 연구원 온보딩

**예상 소요 시간:** 약 1시간

---

### 👨‍🔬 연구원 (시스템 사용자)

**지금 바로 시작 →** [QUICK_START_LAB.md](QUICK_START_LAB.md)

**준비물:**
- ✅ GitHub 계정
- ✅ 연구실 네트워크 접속
- ✅ 웹 브라우저

**시작 단계:**
1. 웹 접속: `http://node3.connectome:3000`
2. GitHub 로그인
3. Repository 연결
4. 대시보드 확인

**예상 소요 시간:** 5분

---

### 👨‍💻 개발자 (시스템 이해/수정)

**지금 바로 시작 →** [README.md](README.md)

**먼저 읽어야 할 문서 순서:**
1. [README.md](README.md) - 전체 시스템 개요
2. [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - 현재 구현 상태
3. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 배포 프로세스
4. 소스 코드 탐색

---

## 📚 전체 문서 목록

### 배포 관련 (관리자용)
| 문서 | 크기 | 용도 |
|------|------|------|
| [ADMIN_DEPLOYMENT_CHECKLIST.md](ADMIN_DEPLOYMENT_CHECKLIST.md) | 8.9K | ⭐ 배포 체크리스트 (시작점) |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | 12K | 상세 배포 가이드 |
| [DEPLOY_CONNECTOME.md](DEPLOY_CONNECTOME.md) | 14K | Connectome 서버 특화 가이드 |
| [DEPLOYMENT_INDEX.md](DEPLOYMENT_INDEX.md) | 5.9K | 문서 네비게이션 |

### 사용자 가이드 (연구원용)
| 문서 | 크기 | 용도 |
|------|------|------|
| [QUICK_START_LAB.md](QUICK_START_LAB.md) | 4.1K | ⭐ 5분 빠른 시작 가이드 |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) (섹션 2-3) | - | 상세 사용법 + FAQ |

### 프로젝트 정보
| 문서 | 용도 |
|------|------|
| [README.md](README.md) | 프로젝트 개요 및 아키텍처 |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | 구현 현황 |

---

## 🛠️ 배포 스크립트

### 자동화 스크립트
```bash
# 1. 배포 전 체크
./deployment/pre-deploy-check.sh

# 2. 서버로 파일 전송
./deployment/deploy.sh

# 3. 서버에서: 데이터베이스 설정
ssh connectome
cd ~/code-monitor/deployment
./setup_db.sh

# 4. 서버에서: SLURM 작업 제출
sbatch backend.slurm
sbatch frontend.slurm

# 5. 데이터베이스 백업 (주간)
./deployment/backup_db.sh
```

---

## ⚡ 빠른 배포 (관리자용)

**5분 만에 배포 준비:**

```bash
# 1. 프로젝트 디렉토리로 이동
cd /Users/jiookcha/Documents/git/Code-Monitor

# 2. 배포 전 체크
./deployment/pre-deploy-check.sh

# 3. GitHub OAuth 앱 생성 (웹 브라우저)
# https://github.com/settings/developers
# → New OAuth App
# → Callback URL: http://node3.connectome:3000/api/auth/callback/github

# 4. Client ID/Secret을 frontend/.env.local에 입력
nano frontend/.env.local

# 5. 서버로 배포
./deployment/deploy.sh

# 6. 서버 SSH 접속
ssh connectome

# 7. 데이터베이스 설정
cd ~/code-monitor/deployment
./setup_db.sh

# 8. 환경 변수 확인 (서버 호스트명 확인)
hostname  # 예: node3
nano ~/code-monitor/frontend/.env.local
# NEXTAUTH_URL=http://node3.connectome:3000 (호스트명 맞게 수정)

# 9. 패키지 설치 및 빌드
cd ~/code-monitor/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate

cd ~/code-monitor/frontend
npm install
npm run build

# 10. 서비스 시작
cd ~/code-monitor/deployment
sbatch backend.slurm
sleep 30
sbatch frontend.slurm

# 11. 확인
squeue -u $USER
curl http://localhost:8000/health
```

**웹 브라우저로 확인:**
- Frontend: http://node3.connectome:3000
- Backend API: http://node3.connectome:8000/docs

---

## 🎯 다음 단계

### ✅ 배포 완료 후

1. **연구원들에게 공지**
   - [QUICK_START_LAB.md](QUICK_START_LAB.md) 문서 전달
   - 접속 URL 공유: `http://node3.connectome:3000`
   - 슬랙/이메일로 안내

2. **테스트 진행**
   - 테스트 계정으로 전체 플로우 검증
   - GitHub 로그인
   - Repository 연결
   - 주간 제출
   - 랭킹 확인

3. **모니터링 설정**
   - 일일 헬스체크: `curl http://localhost:8000/health`
   - 로그 확인: `tail -f ~/code-monitor/logs/*.log`
   - SLURM 작업 상태: `squeue -u $USER`

4. **백업 설정**
   - 주간 백업: `./deployment/backup_db.sh`
   - Cron 작업 등록 (선택사항)

---

## 🚨 문제 해결

### 배포 중 문제가 발생했나요?

**단계별 트러블슈팅:**

1. **배포 전 체크 실패**
   → [ADMIN_DEPLOYMENT_CHECKLIST.md](ADMIN_DEPLOYMENT_CHECKLIST.md) Phase 1 확인

2. **GitHub OAuth 에러**
   → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) Q1 참조

3. **데이터베이스 연결 실패**
   → [ADMIN_DEPLOYMENT_CHECKLIST.md](ADMIN_DEPLOYMENT_CHECKLIST.md) 트러블슈팅 섹션

4. **SLURM 작업 실패**
   → 로그 확인: `tail -100 ~/code-monitor/logs/backend.log`

5. **기타 문제**
   → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) FAQ 섹션 (Q1-Q6)

---

## 📞 지원

### 관리자 지원
- **배포 관련**: ADMIN_DEPLOYMENT_CHECKLIST.md 트러블슈팅
- **기술 문의**: [관리자 이메일]
- **긴급 상황**: [전화번호]

### 연구원 지원
- **사용법 문의**: QUICK_START_LAB.md FAQ
- **로그인 문제**: DEPLOYMENT_GUIDE.md Q1
- **일반 문의**: [Slack #code-monitor]

---

## 🎉 배포 성공 체크리스트

배포가 완료되었는지 확인하세요:

- [ ] Backend 서비스 실행 (`curl http://localhost:8000/health` → `{"status":"healthy"}`)
- [ ] Frontend 접속 가능 (`http://node3.connectome:3000`)
- [ ] GitHub 로그인 작동
- [ ] 대시보드 표시
- [ ] 랭킹 페이지 작동
- [ ] 주간 제출 기능 작동
- [ ] 연구원들이 접속 가능
- [ ] 문서 전달 완료

**모든 항목이 체크되었나요? 축하합니다! 🎊**

**배포 성공! 이제 연구실 생산성 모니터링을 시작하세요!**

---

**Last Updated**: 2025-10-21
**Version**: 1.0
**Maintained by**: Claude Code 🤖
