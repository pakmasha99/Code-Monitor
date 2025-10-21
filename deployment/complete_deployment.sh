#!/bin/bash
# Complete Deployment Script - Run this on Connectome Server
# After deployment/deploy.sh has transferred all files

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================"
echo "Code-Monitor Complete Deployment"
echo "======================================${NC}"

# Get current directory
PROJECT_DIR="$HOME/code-monitor"
cd "$PROJECT_DIR"

# Step 1: Database Migration
echo -e "\n${YELLOW}[1/5] Running database migration...${NC}"
psql postgresql://codemonitor:codemonitor_secure_2025@localhost:5432/codemonitor \
  -f backend/migrations/add_document_lines_added.sql
echo -e "${GREEN}✓ Database migration complete${NC}"

# Step 2: Backend Dependencies
echo -e "\n${YELLOW}[2/5] Installing backend dependencies...${NC}"
cd backend
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Step 3: Frontend Dependencies
echo -e "\n${YELLOW}[3/5] Installing frontend dependencies...${NC}"
cd ../frontend
npm install
npm run build
echo -e "${GREEN}✓ Frontend built${NC}"

# Step 4: Start Services
echo -e "\n${YELLOW}[4/5] Restarting services...${NC}"
cd "$PROJECT_DIR"

# Stop existing Celery workers
pkill -f "celery.*worker" || true
pkill -f "celery.*beat" || true
sleep 2

# Start Celery worker
cd backend
source venv/bin/activate
nohup celery -A app.core.celery_app worker --loglevel=info \
  > ../logs/celery_worker.log 2>&1 &
echo "  Celery worker started (PID: $!)"

# Start Celery beat
nohup celery -A app.core.celery_app beat --loglevel=info \
  > ../logs/celery_beat.log 2>&1 &
echo "  Celery beat started (PID: $!)"

echo -e "${GREEN}✓ Services restarted${NC}"

# Step 5: Restart backend/frontend via SLURM
echo -e "\n${YELLOW}[5/5] Submitting SLURM jobs...${NC}"
cd "$PROJECT_DIR/deployment"

# Cancel existing jobs
scancel -u $USER --name=code-monitor-backend || true
scancel -u $USER --name=code-monitor-frontend || true
sleep 2

# Submit new jobs
sbatch backend.slurm
sbatch frontend.slurm

echo -e "${GREEN}✓ SLURM jobs submitted${NC}"

# Wait for services
echo -e "\n${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Verify deployment
echo -e "\n${GREEN}======================================"
echo "Deployment Complete!"
echo "======================================${NC}"

echo -e "\nService Status:"
echo "  Backend API:    http://localhost:8000"
echo "  Frontend:       http://localhost:3000"
echo "  Celery Worker:  Check logs/celery_worker.log"
echo "  Celery Beat:    Check logs/celery_beat.log"

echo -e "\nNext Steps:"
echo "1. Check SLURM jobs:"
echo "   squeue -u \$USER"
echo ""
echo "2. Test backend:"
echo "   curl http://localhost:8000/health"
echo ""
echo "3. Test frontend:"
echo "   curl http://localhost:3000"
echo ""
echo "4. Run RAG indexing (IMPORTANT!):"
echo "   cd ~/code-monitor/backend"
echo "   source venv/bin/activate"
echo "   python scripts/init_rag_index.py"
echo ""
echo "5. Monitor logs:"
echo "   tail -f ~/code-monitor/logs/backend-*.log"
echo "   tail -f ~/code-monitor/logs/frontend-*.log"
echo ""
echo -e "${YELLOW}⚠️  Don't forget to run RAG indexing to enable Code Q&A feature!${NC}"
