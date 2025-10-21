#!/bin/bash
# RAG Infrastructure Setup Script
# Sets up Redis and Qdrant for Code-Monitor RAG system
# Author: Automated setup for Phase 1
# Date: 2025-10-21

set -e  # Exit on error

echo "🚀 Starting RAG Infrastructure Setup..."
echo "========================================="

# Color codes for output
GREEN='\033[0[32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
RAG_DIR="$HOME/code-monitor/rag"
REDIS_PORT=6379
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334

# Create directory structure
echo -e "${YELLOW}📁 Creating directory structure...${NC}"
mkdir -p "$RAG_DIR"/{redis,qdrant_storage,logs}

# ============================================================
# REDIS SETUP (User-space installation)
# ============================================================
echo -e "${YELLOW}🔧 Setting up Redis server...${NC}"

# Check if Redis is already running
if pgrep -f "redis-server.*$REDIS_PORT" > /dev/null; then
    echo -e "${GREEN}✅ Redis server already running on port $REDIS_PORT${NC}"
else
    # Download and compile Redis from source (user-space)
    cd "$RAG_DIR/redis"

    if [ ! -f "redis-server" ]; then
        echo "Downloading Redis 7.2.4..."
        wget https://download.redis.io/releases/redis-7.2.4.tar.gz
        tar xzf redis-7.2.4.tar.gz
        cd redis-7.2.4
        make
        # Copy binaries to rag/redis directory
        cp src/redis-server src/redis-cli ../../
        cd ../..
        rm -rf redis-7.2.4 redis-7.2.4.tar.gz
    fi

    # Create Redis configuration
    cat > "$RAG_DIR/redis/redis.conf" <<EOF
# Redis configuration for Code-Monitor RAG system
port $REDIS_PORT
bind 127.0.0.1
daemonize yes
pidfile $RAG_DIR/redis/redis.pid
logfile $RAG_DIR/logs/redis.log
dir $RAG_DIR/redis
dbfilename dump.rdb

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Security
protected-mode yes
EOF

    # Start Redis server
    echo "Starting Redis server..."
    "$RAG_DIR/redis/redis-server" "$RAG_DIR/redis/redis.conf"
    sleep 2

    # Verify Redis is running
    if "$RAG_DIR/redis/redis-cli" -p $REDIS_PORT ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis server started successfully on port $REDIS_PORT${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis server${NC}"
        exit 1
    fi
fi

# ============================================================
# QDRANT SETUP (Docker)
# ============================================================
echo -e "${YELLOW}🔧 Setting up Qdrant vector database...${NC}"

# Check if Qdrant container is already running
if docker ps | grep -q "qdrant-code-monitor"; then
    echo -e "${GREEN}✅ Qdrant container already running${NC}"
else
    # Pull Qdrant image
    echo "Pulling Qdrant Docker image..."
    docker pull qdrant/qdrant:latest

    # Stop and remove existing container if it exists
    docker stop qdrant-code-monitor 2>/dev/null || true
    docker rm qdrant-code-monitor 2>/dev/null || true

    # Start Qdrant container
    echo "Starting Qdrant container..."
    docker run -d \
        --name qdrant-code-monitor \
        -p $QDRANT_PORT:6333 \
        -p $QDRANT_GRPC_PORT:6334 \
        -v "$RAG_DIR/qdrant_storage:/qdrant/storage:z" \
        --restart unless-stopped \
        qdrant/qdrant:latest

    sleep 5

    # Verify Qdrant is running
    if curl -s http://localhost:$QDRANT_PORT/collections > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Qdrant started successfully on port $QDRANT_PORT${NC}"
    else
        echo -e "${RED}❌ Failed to start Qdrant${NC}"
        exit 1
    fi
fi

# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================
echo -e "${YELLOW}⚙️  Creating environment configuration...${NC}"

cd "$HOME/code-monitor/backend"

# Create .env file with RAG configuration
cat >> .env <<EOF

# ============================================================
# RAG SYSTEM CONFIGURATION (Added $(date))
# ============================================================

# Redis Configuration
REDIS_HOST=127.0.0.1
REDIS_PORT=$REDIS_PORT
REDIS_DB=0
CELERY_BROKER_URL=redis://127.0.0.1:$REDIS_PORT/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:$REDIS_PORT/1

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=$QDRANT_PORT
QDRANT_COLLECTION_NAME=code_embeddings
QDRANT_VECTOR_SIZE=1536

# LLM API Keys (REQUIRED - Please configure)
# Get Anthropic API key from: https://console.anthropic.com/
# Get OpenAI API key from: https://platform.openai.com/api-keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Code Analysis Configuration
MAX_FILE_SIZE_KB=500
SUPPORTED_LANGUAGES=python,javascript,typescript,java,go,rust
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=claude-3-5-sonnet-20241022

# Background Tasks
CELERY_TASK_ALWAYS_EAGER=False
SYNC_INTERVAL_HOURS=24
MAX_CONCURRENT_ANALYSES=3

EOF

echo -e "${GREEN}✅ Environment configuration created${NC}"

# ============================================================
# HEALTH CHECK
# ============================================================
echo ""
echo "🏥 Infrastructure Health Check"
echo "========================================="

# Redis health
if "$RAG_DIR/redis/redis-cli" -p $REDIS_PORT ping > /dev/null 2>&1; then
    REDIS_STATUS="${GREEN}✅ Running${NC}"
else
    REDIS_STATUS="${RED}❌ Not Running${NC}"
fi

# Qdrant health
if curl -s http://localhost:$QDRANT_PORT/collections > /dev/null 2>&1; then
    QDRANT_STATUS="${GREEN}✅ Running${NC}"
else
    QDRANT_STATUS="${RED}❌ Not Running${NC}"
fi

echo -e "Redis Server:    $REDIS_STATUS (port $REDIS_PORT)"
echo -e "Qdrant Vector DB: $QDRANT_STATUS (port $QDRANT_PORT)"
echo ""

# ============================================================
# MANAGEMENT COMMANDS
# ============================================================
echo "📝 Management Commands"
echo "========================================="
echo "Redis:"
echo "  Status: $RAG_DIR/redis/redis-cli -p $REDIS_PORT ping"
echo "  CLI:    $RAG_DIR/redis/redis-cli -p $REDIS_PORT"
echo "  Stop:   $RAG_DIR/redis/redis-cli -p $REDIS_PORT shutdown"
echo ""
echo "Qdrant:"
echo "  Status: curl http://localhost:$QDRANT_PORT/collections"
echo "  Logs:   docker logs qdrant-code-monitor"
echo "  Stop:   docker stop qdrant-code-monitor"
echo "  Start:  docker start qdrant-code-monitor"
echo ""

# ============================================================
# NEXT STEPS
# ============================================================
echo "✨ Next Steps"
echo "========================================="
echo "1. Configure API keys in backend/.env:"
echo "   - ANTHROPIC_API_KEY (https://console.anthropic.com/)"
echo "   - OPENAI_API_KEY (https://platform.openai.com/api-keys)"
echo ""
echo "2. Install Python dependencies:"
echo "   cd ~/code-monitor/backend"
echo "   source venv/bin/activate"
echo "   pip install anthropic openai qdrant-client tree-sitter celery[redis]"
echo ""
echo "3. Run database migration:"
echo "   alembic revision --autogenerate -m 'Add code_analysis table'"
echo "   alembic upgrade head"
echo ""
echo "4. Test the setup:"
echo "   python -c 'import redis; r=redis.Redis(port=$REDIS_PORT); print(r.ping())'"
echo "   curl http://localhost:$QDRANT_PORT/collections"
echo ""

echo -e "${GREEN}✅ RAG Infrastructure Setup Complete!${NC}"
