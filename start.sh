#!/bin/bash
# Code-Monitor 빠른 시작 스크립트

set -e  # 에러 발생시 중단

echo "🚀 Starting Code-Monitor..."

# 1. Docker 확인
echo "1️⃣ Checking Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo "⚠️  Docker is not running. Starting Docker Desktop..."
    open -a Docker
    echo "⏳ Waiting for Docker to start..."
    sleep 15
fi
echo "✅ Docker is running"

# 2. Docker Compose 시작
echo ""
echo "2️⃣ Starting Docker services..."
docker-compose up -d
echo "⏳ Waiting for services to be healthy..."
sleep 10
docker-compose ps
echo "✅ Docker services started"

# 3. 데이터베이스 초기화 (이미 있으면 스킵)
echo ""
echo "3️⃣ Initializing database..."
python scripts/init_db.py
echo "✅ Database ready"

# 4. API 서버 시작
echo ""
echo "4️⃣ Starting API server..."
echo "📡 API will be available at http://localhost:8000"
echo "📚 Swagger docs at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "─────────────────────────────────────────"

# backend 디렉토리로 이동해서 API 시작
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
