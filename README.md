# Code-Monitor

**연구실 지식 증류 및 생산성 모니터링 시스템**

Lab Knowledge Distillation & Productivity Monitoring System for Research Teams

---

## 📖 Overview

Code-Monitor는 연구실 구성원들의 코드/문서 생성량을 추적하고, LLM과 RAG 기술을 활용하여 팀 전체의 코드 지식을 공유 가능한 지식 베이스로 전환하는 시스템입니다.

**핵심 기능:**
- 📊 실시간 생산성 대시보드 및 랭킹
- 🤖 LLM 기반 자동 코드 분석 및 문서화
- 🔍 Vector DB 기반 의미적 코드 검색 (RAG)
- 📈 종단적 데이터 분석 및 트렌드 추적
- 💬 자연어로 "다른 사람 코드 어떻게 작성했는지" 질의응답
- 🏆 지식 공유 촉진 및 팀 학습 가속화

---

## 🏗️ Architecture

```
Frontend Dashboard (Streamlit/React)
         ↓
Backend API (FastAPI + Celery)
         ↓
PostgreSQL + Qdrant Vector DB
         ↓
Git Repos (20 members) + LLM Analysis
```

**6 Layer Architecture:**
1. **Data Collection** - Manual submission + Automated git analysis
2. **Processing** - LLM code analyzer + Embedding generator
3. **Storage** - PostgreSQL (metrics) + Qdrant (code vectors)
4. **RAG Query** - Semantic search + Knowledge discovery
5. **Analytics** - Real-time dashboard + Longitudinal trends
6. **API** - REST + WebSocket for live updates

---

## 🚀 Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Celery, Redis |
| **Frontend** | Streamlit (MVP) → React |
| **Database** | PostgreSQL, Qdrant |
| **LLM** | Claude 3.5 Sonnet / GPT-4 |
| **Embedding** | OpenAI text-embedding-3-small |
| **Git** | GitPython, GitHub API |
| **Deployment** | Docker, Docker Compose |

---

## 📂 Project Structure

```
Code-Monitor/
├── README.md                          # This file
├── lab-knowledge-system-design.md     # Full system design document
├── backend/                           # FastAPI backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app entry
│   │   ├── api/                      # API routes
│   │   ├── models/                   # SQLAlchemy models
│   │   ├── services/                 # Business logic
│   │   └── tasks/                    # Celery tasks
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                          # Dashboard frontend
│   ├── streamlit_app.py              # Streamlit dashboard
│   └── requirements.txt
├── scripts/                           # Utility scripts
│   ├── init_db.py                    # Database initialization
│   └── seed_data.py                  # Sample data seeding
├── docker-compose.yml                 # Multi-service orchestration
└── docs/                             # Additional documentation
```

---

## 🛠️ Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Git
- OpenAI API key (for embeddings)
- Anthropic API key (for LLM analysis)

### Installation

```bash
# Clone repository
cd /Users/jiookcha/Documents/git/Code-Monitor

# Set up environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (backend)
cd backend
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Start services with Docker Compose
docker-compose up -d

# Initialize database
python scripts/init_db.py

# Run backend
uvicorn app.main:app --reload

# In another terminal, run Celery worker
celery -A app.tasks worker --loglevel=info

# In another terminal, run dashboard
cd frontend
streamlit run streamlit_app.py
```

---

## 📋 Implementation Roadmap

### ✅ Phase 0: Planning (Current)
- [x] System design document
- [x] Architecture planning
- [x] Technology stack selection

### 🔄 Phase 1: MVP (Weeks 1-4)
- [ ] PostgreSQL schema implementation
- [ ] Basic FastAPI backend
- [ ] Manual submission form
- [ ] Git metrics collection
- [ ] Simple leaderboard
- [ ] Streamlit dashboard

### ⏳ Phase 2: Automation (Weeks 5-6)
- [ ] Celery task queue
- [ ] Automated git sync
- [ ] Real-time updates (WebSocket)
- [ ] Email notifications

### ⏳ Phase 3: LLM Integration (Weeks 7-8)
- [ ] LLM code analyzer
- [ ] Automated code summarization
- [ ] Quality metrics generation
- [ ] Enhanced ranking system

### ⏳ Phase 4: RAG System (Weeks 9-10)
- [ ] Qdrant vector database
- [ ] Code embedding pipeline
- [ ] Semantic search
- [ ] RAG query interface

### ⏳ Phase 5: Production (Weeks 11-12)
- [ ] Performance optimization
- [ ] Docker deployment
- [ ] User training
- [ ] Monitoring & logging

---

## 📊 Usage

### For Lab Members

**Weekly Submission:**
1. Navigate to dashboard
2. Click "Submit Weekly Report"
3. Review auto-detected git metrics
4. Add manual document counts
5. Write weekly notes
6. Submit

**Code Discovery (RAG):**
1. Go to "Code Explorer" tab
2. Ask natural language questions:
   - "누가 데이터 전처리 파이프라인 만들었어?"
   - "효율적인 정렬 알고리즘 구현 예시는?"
   - "Transformer 모델 구현한 사람 있어?"
3. Review code examples with attribution
4. Ask follow-up questions

### For Advisors

**Analytics:**
- View team-wide productivity trends
- Identify top performers
- Monitor longitudinal progress
- Export data for reports

**Admin:**
- Manage user accounts
- Configure git repositories
- Adjust ranking weights
- Monitor system health

---

## 🤝 Contributing

This is an internal research lab project. For implementation questions:

- **Documentation:** See `lab-knowledge-system-design.md`
- **Issues:** Create GitHub issues for bugs/features
- **Development:** Create feature branches, submit PRs

---

## 📄 License

Internal use only - Research Lab Project

---

## 📞 Contact

- **Project Lead:** [Your Name]
- **Technical Support:** [Developer Name]
- **Slack:** #code-monitor

---

## 🎯 Project Goals

1. **Transparency** - Every member sees their contributions in real-time
2. **Learning Acceleration** - Instantly discover best practices from teammates
3. **Knowledge Preservation** - Individual code experience becomes collective team knowledge
4. **Motivation** - Healthy competition and recognition drives continuous improvement

---

**Built with Claude Code 🤖**
