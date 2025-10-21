#!/bin/bash

# Code-Monitor Quick Deployment Script
# This script automates the deployment to Connectome server

set -e

SERVER="server"
REMOTE_DIR="~/code-monitor"
LOCAL_PROJECT="/Users/jiookcha/Documents/git/Code-Monitor"

echo "=== Code-Monitor Deployment Script ==="
echo "Target: Connectome Server"
echo "======================================="

# Step 1: Create remote directories
echo "[1/5] Creating remote directories..."
ssh ${SERVER} "mkdir -p ${REMOTE_DIR}/{backend,frontend,deployment,logs}"

# Step 2: Transfer backend
echo "[2/5] Transferring backend files..."
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
    ${LOCAL_PROJECT}/backend/ ${SERVER}:${REMOTE_DIR}/backend/

# Step 3: Transfer frontend
echo "[3/5] Transferring frontend files..."
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '.env.local' \
    ${LOCAL_PROJECT}/frontend/ ${SERVER}:${REMOTE_DIR}/frontend/

# Step 4: Transfer deployment scripts
echo "[4/5] Transferring deployment scripts..."
rsync -avz ${LOCAL_PROJECT}/deployment/ ${SERVER}:${REMOTE_DIR}/deployment/
ssh ${SERVER} "chmod +x ${REMOTE_DIR}/deployment/*.sh"

# Step 5: Display next steps
echo "[5/5] Transfer complete!"
echo ""
echo "======================================="
echo "Deployment files transferred successfully!"
echo ""
echo "Next steps (run on Connectome server):"
echo ""
echo "1. SSH to server:"
echo "   ssh ${SERVER}"
echo ""
echo "2. Setup database:"
echo "   cd ~/code-monitor/deployment"
echo "   bash setup_db.sh"
echo ""
echo "3. Configure environment variables:"
echo "   # Backend"
echo "   vi ~/code-monitor/backend/.env"
echo "   # Add: DATABASE_URL=postgresql://codemonitor:password@localhost:5432/codemonitor"
echo ""
echo "   # Frontend"
echo "   vi ~/code-monitor/frontend/.env.local"
echo "   # Add: NEXTAUTH_URL, GITHUB_CLIENT_ID, NEXT_PUBLIC_API_URL"
echo ""
echo "4. Submit SLURM jobs:"
echo "   cd ~/code-monitor/deployment"
echo "   sbatch backend.slurm"
echo "   sbatch frontend.slurm"
echo ""
echo "5. Monitor jobs:"
echo "   squeue -u \$USER"
echo "   tail -f ~/code-monitor/logs/backend-*.log"
echo "   tail -f ~/code-monitor/logs/frontend-*.log"
echo ""
echo "6. Test deployment:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:3000"
echo ""
echo "======================================="
echo "For detailed instructions, see:"
echo "${LOCAL_PROJECT}/DEPLOY_CONNECTOME.md"
echo "======================================="
