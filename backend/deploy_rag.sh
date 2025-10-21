#!/bin/bash
# RAG System Deployment Script for Connectome Server
# Run this on the server after pulling latest code

set -e  # Exit on error

echo "🚀 Starting RAG System Deployment..."
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check we're in the right directory
echo -e "${YELLOW}Step 1: Checking directory...${NC}"
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}Error: Not in backend directory!${NC}"
    echo "Please run from Code-Monitor/backend/"
    exit 1
fi
echo -e "${GREEN}✓ In correct directory${NC}"

# Step 2: Pull latest code
echo -e "${YELLOW}Step 2: Pulling latest code from main...${NC}"
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"

# Step 3: Activate virtual environment
echo -e "${YELLOW}Step 3: Activating virtual environment...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}Error: venv not found!${NC}"
    echo "Creating new virtual environment..."
    python3.11 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment created and activated${NC}"
fi

# Step 4: Install dependencies
echo -e "${YELLOW}Step 4: Installing new dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 5: Verify rank-bm25 installation
echo -e "${YELLOW}Step 5: Verifying rank-bm25...${NC}"
if pip show rank-bm25 > /dev/null 2>&1; then
    VERSION=$(pip show rank-bm25 | grep Version | cut -d' ' -f2)
    echo -e "${GREEN}✓ rank-bm25 ${VERSION} installed${NC}"
else
    echo -e "${RED}Error: rank-bm25 not installed!${NC}"
    exit 1
fi

# Step 6: Check if Qdrant is running
echo -e "${YELLOW}Step 6: Checking Qdrant vector database...${NC}"
if curl -s http://localhost:6333 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Qdrant is already running${NC}"
else
    echo -e "${YELLOW}Starting Qdrant...${NC}"
    docker run -d \
        --name qdrant \
        -p 6333:6333 \
        -v $(pwd)/qdrant_storage:/qdrant/storage \
        qdrant/qdrant

    echo "Waiting for Qdrant to start..."
    sleep 5

    if curl -s http://localhost:6333 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Qdrant started successfully${NC}"
    else
        echo -e "${RED}Error: Could not start Qdrant!${NC}"
        exit 1
    fi
fi

# Step 7: Check Redis
echo -e "${YELLOW}Step 7: Checking Redis...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}Warning: Redis not responding!${NC}"
    echo "Make sure Redis is running: sudo systemctl start redis"
fi

# Step 8: Stop existing Celery workers (if any)
echo -e "${YELLOW}Step 8: Stopping existing Celery processes...${NC}"
pkill -f "celery.*worker" || true
pkill -f "celery.*beat" || true
sleep 2
echo -e "${GREEN}✓ Old Celery processes stopped${NC}"

# Step 9: Start Celery worker
echo -e "${YELLOW}Step 9: Starting Celery worker...${NC}"
nohup celery -A app.core.celery_app worker --loglevel=info \
    > logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo -e "${GREEN}✓ Celery worker started (PID: ${WORKER_PID})${NC}"

# Step 10: Start Celery beat (scheduler)
echo -e "${YELLOW}Step 10: Starting Celery beat...${NC}"
nohup celery -A app.core.celery_app beat --loglevel=info \
    > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo -e "${GREEN}✓ Celery beat started (PID: ${BEAT_PID})${NC}"

# Step 11: Restart FastAPI application
echo -e "${YELLOW}Step 11: Restarting FastAPI application...${NC}"

# Try systemd first
if systemctl list-units --type=service | grep -q "code-monitor"; then
    sudo systemctl restart code-monitor
    echo -e "${GREEN}✓ FastAPI restarted via systemd${NC}"
# Try supervisorctl
elif command -v supervisorctl > /dev/null 2>&1; then
    sudo supervisorctl restart code-monitor
    echo -e "${GREEN}✓ FastAPI restarted via supervisor${NC}"
else
    echo -e "${YELLOW}Manual restart required${NC}"
    echo "Please restart your FastAPI application manually"
fi

# Step 12: Wait for services to start
echo -e "${YELLOW}Step 12: Waiting for services to initialize...${NC}"
sleep 5

# Step 13: Verify deployment
echo -e "${YELLOW}Step 13: Verifying RAG endpoints...${NC}"

# Check main app
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ FastAPI is responding${NC}"
else
    echo -e "${RED}⚠ FastAPI not responding on port 8000${NC}"
fi

# Check RAG status endpoint
if curl -s http://localhost:8000/api/v1/rag/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ RAG endpoints are live${NC}"

    # Show status
    STATUS=$(curl -s http://localhost:8000/api/v1/rag/status)
    echo ""
    echo "RAG System Status:"
    echo "$STATUS" | python3 -m json.tool 2>/dev/null || echo "$STATUS"
else
    echo -e "${RED}⚠ RAG endpoints not responding${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "======================================"
echo ""
echo "Service Status:"
echo "  - Qdrant:       http://localhost:6333"
echo "  - FastAPI:      http://localhost:8000"
echo "  - RAG API:      http://localhost:8000/api/v1/rag/*"
echo "  - Celery Worker: Running (PID: ${WORKER_PID})"
echo "  - Celery Beat:   Running (PID: ${BEAT_PID})"
echo ""
echo "Logs:"
echo "  - Celery Worker: logs/celery_worker.log"
echo "  - Celery Beat:   logs/celery_beat.log"
echo ""
echo "Next Steps:"
echo "  1. Test RAG search:"
echo "     curl -X POST http://localhost:8000/api/v1/rag/search \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"query\": \"test\", \"limit\": 5, \"search_type\": \"bm25\"}'"
echo ""
echo "  2. Trigger initial indexing:"
echo "     curl -X POST http://localhost:8000/api/v1/rag/reindex \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"repository_id\": 1}'"
echo ""
echo "  3. Check logs:"
echo "     tail -f logs/celery_worker.log"
echo ""
