#!/bin/bash

# Code-Monitor 배포 전 체크리스트
# 이 스크립트를 실행하여 배포 준비가 완료되었는지 확인하세요

echo "=================================="
echo "Code-Monitor Pre-Deployment Check"
echo "=================================="
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass=0
check_fail=0

# 함수: 체크 항목 출력
check_item() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((check_pass++))
    else
        echo -e "${RED}✗${NC} $2"
        ((check_fail++))
    fi
}

echo "1. 로컬 파일 확인"
echo "----------------------------"

# Backend 파일 확인
[ -f "backend/app/main.py" ]
check_item $? "Backend main.py 존재"

[ -f "backend/requirements.txt" ]
check_item $? "Backend requirements.txt 존재"

[ -f "backend/.env" ]
check_item $? "Backend .env 파일 존재 (없으면 .env.example 복사 필요)"

# Frontend 파일 확인
[ -f "frontend/package.json" ]
check_item $? "Frontend package.json 존재"

[ -f "frontend/.env.local" ]
check_item $? "Frontend .env.local 파일 존재 (없으면 생성 필요)"

# SLURM 스크립트 확인
[ -f "deployment/backend.slurm" ]
check_item $? "Backend SLURM 스크립트 존재"

[ -f "deployment/frontend.slurm" ]
check_item $? "Frontend SLURM 스크립트 존재"

echo ""
echo "2. 환경 변수 확인"
echo "----------------------------"

# Backend .env 확인
if [ -f "backend/.env" ]; then
    grep -q "DATABASE_URL=" backend/.env
    check_item $? "DATABASE_URL 설정됨"
    
    grep -q "SECRET_KEY=" backend/.env
    check_item $? "SECRET_KEY 설정됨"
    
    grep -q "CORS_ORIGINS=" backend/.env
    check_item $? "CORS_ORIGINS 설정됨"
else
    echo -e "${YELLOW}⚠${NC} backend/.env 파일이 없습니다. .env.example을 복사하여 설정하세요."
    ((check_fail+=3))
fi

# Frontend .env.local 확인
if [ -f "frontend/.env.local" ]; then
    grep -q "NEXTAUTH_URL=" frontend/.env.local
    check_item $? "NEXTAUTH_URL 설정됨"
    
    grep -q "NEXTAUTH_SECRET=" frontend/.env.local
    check_item $? "NEXTAUTH_SECRET 설정됨"
    
    grep -q "GITHUB_CLIENT_ID=" frontend/.env.local
    check_item $? "GITHUB_CLIENT_ID 설정됨"
    
    grep -q "GITHUB_CLIENT_SECRET=" frontend/.env.local
    check_item $? "GITHUB_CLIENT_SECRET 설정됨"
    
    grep -q "NEXT_PUBLIC_API_URL=" frontend/.env.local
    check_item $? "NEXT_PUBLIC_API_URL 설정됨"
else
    echo -e "${YELLOW}⚠${NC} frontend/.env.local 파일이 없습니다. 생성이 필요합니다."
    ((check_fail+=5))
fi

echo ""
echo "3. Git 상태 확인"
echo "----------------------------"

git diff --quiet
check_item $? "Working directory가 clean 상태 (커밋되지 않은 변경사항 없음)"

git diff --cached --quiet
check_item $? "Staging area가 clean 상태"

echo ""
echo "=================================="
echo "체크 결과 요약"
echo "=================================="
echo -e "${GREEN}통과: $check_pass${NC}"
echo -e "${RED}실패: $check_fail${NC}"
echo ""

if [ $check_fail -eq 0 ]; then
    echo -e "${GREEN}✓ 배포 준비 완료!${NC}"
    echo ""
    echo "다음 명령어로 배포를 진행하세요:"
    echo "  ./deployment/deploy.sh"
    exit 0
else
    echo -e "${RED}✗ 배포 전 $check_fail 개 항목을 수정해야 합니다.${NC}"
    echo ""
    echo "상세한 설정 방법은 DEPLOYMENT_GUIDE.md를 참조하세요."
    exit 1
fi
