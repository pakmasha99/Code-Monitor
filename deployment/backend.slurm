#!/bin/bash
#SBATCH --job-name=code-monitor-backend
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=24:00:00
#SBATCH --output=logs/backend-%j.log
#SBATCH --error=logs/backend-%j.err

# Code-Monitor Backend SLURM Job Script
# FastAPI + PostgreSQL
# Resource Allocation: 2 CPUs, 4GB RAM

set -e  # Exit on error

echo "=== Code-Monitor Backend Job Started ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "Start Time: $(date)"
echo "========================================"

# Set working directory
cd ~/code-monitor/backend || exit 1

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "[INFO] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Load environment variables
if [ -f ".env" ]; then
    echo "[INFO] Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
else
    echo "[WARNING] .env file not found, using defaults"
fi

# Run database migrations
echo "[INFO] Running database migrations..."
alembic upgrade head

# Start FastAPI server with Uvicorn
echo "[INFO] Starting FastAPI server on port 8000..."
echo "[INFO] Workers: 2"
echo "[INFO] Host: 0.0.0.0"
echo "========================================"

# Run server
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info

echo "========================================"
echo "Backend server stopped at $(date)"
echo "Job ID: $SLURM_JOB_ID completed"
