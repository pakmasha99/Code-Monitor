#!/bin/bash

# Code-Monitor PostgreSQL Database Setup Script
# Run this script on Connectome server to initialize database

set -e

echo "=== Code-Monitor Database Setup ==="
echo "Setting up PostgreSQL database..."
echo "===================================="

# Database configuration
DB_NAME="codemonitor"
DB_USER="codemonitor"
DB_PASSWORD="codemonitor_secure_2025"  # Change this in production!

# Check if PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    echo "[ERROR] PostgreSQL is not running"
    echo "Please start PostgreSQL: sudo systemctl start postgresql"
    exit 1
fi

echo "[INFO] PostgreSQL is running"

# Create database and user
echo "[INFO] Creating database and user..."
sudo -u postgres psql << EOF
-- Drop existing database and user if they exist (for clean setup)
DROP DATABASE IF EXISTS ${DB_NAME};
DROP USER IF EXISTS ${DB_USER};

-- Create new user
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';

-- Create database
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};

-- Connect to database and grant schema privileges
\c ${DB_NAME}
GRANT ALL ON SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};

\q
EOF

if [ $? -eq 0 ]; then
    echo "[SUCCESS] Database created successfully"
    echo "Database: ${DB_NAME}"
    echo "User: ${DB_USER}"
    echo "Password: ${DB_PASSWORD}"
else
    echo "[ERROR] Failed to create database"
    exit 1
fi

# Test connection
echo ""
echo "[INFO] Testing database connection..."
PGPASSWORD=${DB_PASSWORD} psql -h localhost -U ${DB_USER} -d ${DB_NAME} -c "SELECT version();" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "[SUCCESS] Database connection test passed"
else
    echo "[ERROR] Database connection test failed"
    exit 1
fi

# Display connection string
echo ""
echo "===================================="
echo "Database setup complete!"
echo ""
echo "Connection string for backend .env:"
echo "DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with the DATABASE_URL above"
echo "2. Run migrations: cd ~/code-monitor/backend && alembic upgrade head"
echo "3. Submit SLURM jobs: sbatch deployment/backend.slurm && sbatch deployment/frontend.slurm"
echo "===================================="
