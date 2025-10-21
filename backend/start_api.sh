#!/bin/bash
# Backend API 시작 스크립트

echo "🚀 Starting Code-Monitor API..."
echo ""
echo "📡 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "💚 Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo "─────────────────────────────────────────"

# backend 디렉토리에서 실행
cd "$(dirname "$0")"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
