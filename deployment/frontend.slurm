#!/bin/bash
#SBATCH --job-name=code-monitor-frontend
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=24:00:00
#SBATCH --output=logs/frontend-%j.log
#SBATCH --error=logs/frontend-%j.err

# Code-Monitor Frontend SLURM Job Script
# Next.js 15 Application
# Resource Allocation: 2 CPUs, 4GB RAM

set -e  # Exit on error

echo "=== Code-Monitor Frontend Job Started ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "Start Time: $(date)"
echo "========================================"

# Set working directory
cd ~/code-monitor/frontend || exit 1

# Load environment variables
if [ -f ".env.local" ]; then
    echo "[INFO] Loading environment variables from .env.local"
    export $(grep -v '^#' .env.local | xargs)
else
    echo "[WARNING] .env.local file not found, using defaults"
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "[INFO] Installing npm dependencies..."
    npm install
else
    echo "[INFO] node_modules exists, skipping installation"
fi

# Build for production (recommended for SLURM deployment)
echo "[INFO] Building Next.js application for production..."
npm run build

# Start Next.js server in production mode
echo "[INFO] Starting Next.js server on port 3000..."
echo "[INFO] Mode: production"
echo "[INFO] Host: 0.0.0.0"
echo "========================================"

# Run production server
PORT=3000 npm run start

echo "========================================"
echo "Frontend server stopped at $(date)"
echo "Job ID: $SLURM_JOB_ID completed"
