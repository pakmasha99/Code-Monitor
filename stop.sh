#!/bin/bash
# Code-Monitor 종료 스크립트

echo "🛑 Stopping Code-Monitor..."

# 1. API 서버 종료
echo "1️⃣ Stopping API server..."
pkill -f "uvicorn app.main:app" || echo "API server not running"
echo "✅ API server stopped"

# 2. Docker 서비스 종료
echo ""
echo "2️⃣ Stopping Docker services..."
docker-compose down
echo "✅ Docker services stopped"

echo ""
echo "✅ Code-Monitor stopped successfully"
echo ""
echo "💡 To start again, run: ./start.sh"
