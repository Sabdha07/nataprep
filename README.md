# NATAPrep 2026 — AI-Powered Adaptive Learning Platform

> A self-improving, agent-driven platform to help students score **120/120** in NATA Aptitude and achieve top-tier Drawing scores.

---

## 🏗️ Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                     NATAPrep 2026                        │
├──────────────┬──────────────────────┬────────────────────┤
│  Next.js 14  │   FastAPI (Python)   │   AI Agents        │
│  TypeScript  │   PostgreSQL         │   Claude API       │
│  Tailwind    │   Redis              │   Celery Workers   │
└──────────────┴──────────────────────┴────────────────────┘
```

**8 Specialized AI Agents:**
| Agent | Role |
|-------|------|
| `SyllabusAgent` | Scrapes + parses NATA syllabus, detects updates |
| `QuestionIngestionAgent` | Scrapes past papers, tags and deduplicates |
| `QuestionGenerationAgent` | Generates new questions via Claude |
| `DrawingTaskAgent` | Generates infinite drawing prompts |
| `DrawingEvaluationAgent` | Evaluates drawings via Claude Vision |
| `AdaptiveAgent` | Selects optimal next question (ELO + SM-2) |
| `AnalyticsAgent` | Generates insights, predicted scores |
| `UpdateAgent` | Daily health check, triggers sub-agents |

---

## ⚡ Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker Desktop
- An OpenAI API key

### 1. Start Infrastructure

```bash
cd infra
docker-compose up -d postgres redis
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY and set SECRET_KEY

# Run database migrations
alembic upgrade head

# Seed concept graph (29 concepts + skills)
python -m scripts.seed_concepts

# Seed initial question bank (17 verified questions)
python -m scripts.seed_questions

# Seed drawing tasks (14 curated prompts)
python -m scripts.seed_drawing_tasks

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

App available at: http://localhost:3000

### 4. (Optional) Celery Workers

```bash
cd backend
# In a separate terminal
celery -A app.tasks.celery_app worker --loglevel=info

# Celery Beat scheduler (periodic agents)
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## 🗄️ Database Schema

```
users                     — Student accounts, roles
concepts                  — NATA concept graph (hierarchical)
concept_dependencies      — Prerequisite graph edges
drawing_skills            — Drawing evaluation skill tree
questions                 — Question bank (MCQ/MSQ/Numerical)
question_concepts         — Question ↔ Concept many-to-many
drawing_tasks             — Drawing prompts with rubrics
drawing_submissions       — Student drawing uploads
drawing_evaluations       — Claude Vision evaluation results
practice_sessions         — Practice session tracking
question_attempts         — Per-question attempt log
user_mastery              — Per-concept mastery scores (0.0–1.0)
mistake_log               — Error pattern tracking
syllabus_versions         — Versioned syllabus snapshots
agent_runs                — Agent execution history
```

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

### Authentication
```
POST /auth/register     Create account
POST /auth/login        Login → returns JWT tokens
GET  /auth/me           Current user profile
```

### Practice
```
POST /practice/sessions              Create session (adaptive/concept/mock_test)
GET  /practice/next-question         Get next adaptive question
POST /practice/sessions/{id}/submit  Submit answer → returns result + mastery delta
POST /practice/sessions/{id}/end     End session
```

### Drawing
```
GET  /drawing/tasks/next             Get next drawing task
POST /drawing/submit                 Upload drawing (multipart) → triggers evaluation
GET  /drawing/submissions/{id}/evaluation   Get evaluation result
```

### Analytics
```
GET /analytics/dashboard    Full dashboard (mastery, predictions, insights)
GET /analytics/weak-areas   Prioritised weak areas with recommendations
GET /analytics/predictions  Predicted NATA score breakdown
GET /analytics/progress     Progress over time
```

### Admin
```
POST /admin/agents/generate-questions       Trigger AI question generation
POST /admin/agents/generate-drawing-tasks   Trigger drawing task generation
GET  /admin/agents/runs                     Agent run history
GET  /admin/stats                           Platform statistics
```

---

## 🤖 AI Agents — How They Work

### Adaptive Learning Algorithm (ELO-inspired)
```python
# After each answer:
expected = 1 / (1 + 10^((difficulty - mastery) / 0.4))
delta = K * (actual - expected) * time_factor
new_mastery = clamp(old_mastery + delta, 0.0, 1.0)
```

### Question Selection Priority
```
score = (1 - mastery) × 0.6       # weakest first
      + (review_urgency) × 0.4    # overdue for spaced repetition
```

### Spaced Repetition (SM-2 variant)
| Mastery | Next Review |
|---------|------------|
| < 40%   | 1 day      |
| 40–60%  | 3 days     |
| 60–80%  | 7 days     |
| ≥ 80%   | 14 days    |

### Drawing Evaluation Rubric (100 pts)
| Dimension  | Weight |
|------------|--------|
| Perspective | 25% |
| Proportion  | 20% |
| Composition | 25% |
| Creativity  | 15% |
| Execution   | 15% |

---

## 📁 Project Structure

```
nataprep/
├── backend/
│   ├── app/
│   │   ├── agents/          # 8 AI agents
│   │   ├── api/v1/          # FastAPI routes
│   │   ├── core/            # Config, security, LLM client
│   │   ├── db/models/       # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── tasks/           # Celery workers + scheduled tasks
│   │   └── utils/           # Scraper, deduplicator, embeddings
│   └── scripts/             # Seed data scripts
├── frontend/
│   └── src/
│       ├── app/             # Next.js App Router pages
│       ├── components/      # Shared UI components
│       ├── lib/             # API client, utilities
│       └── store/           # Zustand state management
├── infra/
│   ├── docker-compose.yml   # Full stack orchestration
│   └── nginx/               # Production reverse proxy
└── docs/
    └── ARCHITECTURE.md      # Full system design document
```

---

## 🚀 Production Deployment

### Docker Compose (Full Stack)
```bash
cd infra

# Create .env with production values
cat > .env << 'EOF'
OPENAI_API_KEY=sk-...
SECRET_KEY=your-32-char-secret-key-here
EOF

# Start everything
docker-compose up -d

# Run migrations + seed
docker exec nataprep_backend alembic upgrade head
docker exec nataprep_backend python -m scripts.seed_concepts
docker exec nataprep_backend python -m scripts.seed_questions
docker exec nataprep_backend python -m scripts.seed_drawing_tasks
```

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for question gen + drawing eval (GPT-4o) |
| `SECRET_KEY` | ✅ | JWT signing secret (min 32 chars) |
| `DATABASE_URL` | ✅ | PostgreSQL async URL |
| `REDIS_URL` | ✅ | Redis URL for cache + Celery |
| `QDRANT_URL` | Optional | Vector DB for Phase 2 semantic search |

---

## 📋 Implementation Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Done | Core backend, DB, auth, question system, basic UI |
| Phase 2 | 🔄 Next | Full adaptive engine, analytics, spaced repetition |
| Phase 3 | 📅 Planned | AI agents (syllabus scraping, question generation) |
| Phase 4 | 📅 Planned | Drawing evaluation (Claude Vision), skill tracking |
| Phase 5 | 📅 Planned | Vector DB (Qdrant), semantic search, performance tuning |

---

## 🔑 Creating an Admin User

```bash
# After starting the backend, use the API or run this helper:
cd backend
python -c "
import asyncio
from app.db.base import AsyncSessionLocal
from app.db.models.user import User, UserRole
from app.core.security import hash_password

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            email='admin@nataprep.com',
            hashed_password=hash_password('admin123'),
            full_name='Admin',
            role=UserRole.admin,
        )
        db.add(admin)
        await db.commit()
        print('Admin created: admin@nataprep.com / admin123')

asyncio.run(create_admin())
"
```

---

## 🛠️ Common Commands

```bash
# Generate questions for a specific concept (via API)
curl -X POST "http://localhost:8000/api/v1/admin/agents/generate-questions?count=10&difficulty=0.5" \
  -H "Authorization: Bearer <admin_token>"

# Run update agent manually
curl -X POST "http://localhost:8000/api/v1/admin/agents/generate-drawing-tasks?count=5" \
  -H "Authorization: Bearer <admin_token>"

# Create new migration
cd backend && alembic revision --autogenerate -m "description"

# Apply migrations
cd backend && alembic upgrade head
```

---

## 🎯 Success Metrics

The platform succeeds when:
- ✅ Users can practice every NATA 2026 concept
- ✅ Adaptive engine correctly identifies and targets weak areas
- ✅ Drawing evaluation feedback feels specific and actionable
- ✅ Predicted scores correlate with actual exam performance
- ✅ Question bank grows autonomously via AI agents
- ✅ Syllabus updates are detected and reflected automatically
