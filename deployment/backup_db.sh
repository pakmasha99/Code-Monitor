#!/bin/bash

# PostgreSQL Database Backup Script for Code-Monitor
# 데이터베이스 백업 스크립트

BACKUP_DIR=~/code-monitor/backups
DB_NAME=codemonitor
DB_USER=codemonitor
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/codemonitor_backup_${TIMESTAMP}.sql"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "==================================="
echo "Code-Monitor Database Backup"
echo "==================================="
echo ""

# 백업 디렉토리 생성
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Creating backup directory...${NC}"
    mkdir -p "$BACKUP_DIR"
fi

# PostgreSQL 서비스 확인
echo "[1/4] Checking PostgreSQL service..."
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not running${NC}"
    exit 1
fi

# 데이터베이스 백업
echo "[2/4] Creating database backup..."
PGPASSWORD=codemonitor_secure_2025 pg_dump -h localhost -U $DB_USER $DB_NAME > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

# 백업 파일 압축
echo "[3/4] Compressing backup..."
gzip "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup compressed: ${BACKUP_FILE}.gz${NC}"
else
    echo -e "${RED}✗ Compression failed${NC}"
fi

# 오래된 백업 삭제 (30일 이상)
echo "[4/4] Cleaning old backups (older than 30 days)..."
find "$BACKUP_DIR" -name "codemonitor_backup_*.sql.gz" -mtime +30 -delete

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Old backups cleaned${NC}"
fi

# 백업 크기 확인
BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
echo ""
echo "==================================="
echo "Backup Summary"
echo "==================================="
echo "File: ${BACKUP_FILE}.gz"
echo "Size: $BACKUP_SIZE"
echo "Timestamp: $TIMESTAMP"
echo ""

# 현재 백업 목록
echo "Recent backups:"
ls -lht "$BACKUP_DIR" | head -6

echo ""
echo -e "${GREEN}✓ Backup completed successfully!${NC}"
