# NATAPrep 2026 — Full System Architecture

> Production-grade AI-powered adaptive learning platform for NATA (National Aptitude Test in Architecture)

---

## 1. SYSTEM OVERVIEW

NATAPrep is a **self-improving, agent-driven, adaptive learning system** built to help students achieve 120/120 in NATA Aptitude and top-tier Drawing scores. It is not a static quiz app — it is a living platform powered by autonomous AI agents.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          NATAPrep Platform                          │
├──────────────┬──────────────────────────────┬───────────────────────┤
│   FRONTEND   │          BACKEND API          │      AI AGENTS        │
│  Next.js 14  │       FastAPI (Python)        │   (Async Workers)     │
│  TypeScript  │     Modular Monolith          │   Celery + Redis      │
│  Tailwind    │     PostgreSQL + Qdrant       │   Claude API          │
└──────────────┴──────────────────────────────┴───────────────────────┘
```

---

## 2. TECH STACK

| Layer           | Technology                              | Reason                                       |
|-----------------|-----------------------------------------|----------------------------------------------|
| Frontend        | Next.js 14 (App Router), TypeScript     | SSR, file-based routing, React ecosystem     |
| Styling         | Tailwind CSS + shadcn/ui                | Fast, consistent, accessible components      |
| Drawing Canvas  | Fabric.js + react-canvas-draw           | Rich canvas + upload support                 |
| Backend         | Python 3.12 + FastAPI                   | Async, fast, Pythonic for AI integration     |
| ORM             | SQLAlchemy 2.0 + Alembic                | Type-safe, migration-ready                   |
| Primary DB      | PostgreSQL 16                           | Relational integrity, JSONB for flexible data|
| Vector DB       | Qdrant                                  | Semantic search, concept embeddings          |
| Cache / Queue   | Redis 7                                 | Task queue (Celery), session cache           |
| Background Jobs | Celery + Celery Beat                    | Periodic agents, async task processing       |
| AI Model        | OpenAI GPT-4o                           | LLM for generation, evaluation, tagging      |
| Vision Model    | OpenAI GPT-4o Vision                    | Drawing analysis and scoring                 |
| Embeddings      | OpenAI text-embedding-3-small           | Concept similarity, duplicate detection      |
| Auth            | JWT (python-jose) + bcrypt              | Stateless, secure                            |
| File Storage    | Local (dev) / S3-compatible (prod)      | Drawing uploads, media                       |
| Containerization| Docker + Docker Compose                 | Reproducible environments                    |
| Reverse Proxy   | Nginx                                   | SSL termination, load balancing              |

---

## 3. DIRECTORY STRUCTURE

```
nataprep/
├── backend/
│   ├── app/
│   │   ├── agents/                  # All AI agents
│   │   │   ├── base_agent.py
│   │   │   ├── syllabus_agent.py
│   │   │   ├── ingestion_agent.py
│   │   │   ├── question_gen_agent.py
│   │   │   ├── drawing_task_agent.py
│   │   │   ├── drawing_eval_agent.py
│   │   │   ├── adaptive_agent.py
│   │   │   ├── analytics_agent.py
│   │   │   └── update_agent.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py
│   │   │       │   ├── users.py
│   │   │       │   ├── questions.py
│   │   │       │   ├── drawing.py
│   │   │       │   ├── practice.py
│   │   │       │   ├── analytics.py
│   │   │       │   ├── admin.py
│   │   │       │   └── agents.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py            # Settings (pydantic-settings)
│   │   │   ├── security.py          # JWT, hashing
│   │   │   ├── llm.py               # Claude client wrapper
│   │   │   ├── events.py            # Startup/shutdown events
│   │   │   └── exceptions.py
│   │   ├── db/
│   │   │   ├── models/              # SQLAlchemy models
│   │   │   │   ├── user.py
│   │   │   │   ├── concept.py
│   │   │   │   ├── question.py
│   │   │   │   ├── drawing.py
│   │   │   │   ├── attempt.py
│   │   │   │   ├── mastery.py
│   │   │   │   └── session.py
│   │   │   ├── migrations/          # Alembic migrations
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── schemas/                 # Pydantic schemas (request/response)
│   │   ├── services/                # Business logic layer
│   │   │   ├── user_service.py
│   │   │   ├── question_service.py
│   │   │   ├── drawing_service.py
│   │   │   ├── practice_service.py
│   │   │   ├── adaptive_service.py
│   │   │   └── analytics_service.py
│   │   ├── utils/
│   │   │   ├── scraper.py
│   │   │   ├── embeddings.py
│   │   │   └── deduplicator.py
│   │   ├── tasks/
│   │   │   ├── celery_app.py
│   │   │   └── scheduled_tasks.py
│   │   └── main.py
│   ├── tests/
│   ├── scripts/
│   │   ├── seed_concepts.py
│   │   └── seed_questions.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/login/
│   │   │   ├── (auth)/register/
│   │   │   ├── dashboard/
│   │   │   ├── practice/
│   │   │   │   ├── aptitude/
│   │   │   │   ├── drawing/
│   │   │   │   └── mock-test/
│   │   │   ├── analytics/
│   │   │   ├── concepts/
│   │   │   └── admin/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── store/                   # Zustand state management
│   │   └── types/
│   ├── package.json
│   └── Dockerfile
├── docs/
├── infra/
│   ├── docker-compose.yml
│   └── nginx/
└── .env.example
```

---

## 4. DATABASE SCHEMA

### 4.1 Core Tables

```sql
-- Users
users (
  id UUID PK,
  email VARCHAR UNIQUE NOT NULL,
  hashed_password VARCHAR NOT NULL,
  full_name VARCHAR,
  target_year INT DEFAULT 2026,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  role ENUM('student', 'admin') DEFAULT 'student'
)

-- Concepts (Aptitude knowledge graph nodes)
concepts (
  id UUID PK,
  name VARCHAR NOT NULL,
  description TEXT,
  parent_id UUID FK(concepts.id),  -- hierarchical
  category ENUM('mathematics', 'physics', 'general_aptitude', 'architecture_gk', 'visual_reasoning'),
  syllabus_weight FLOAT,            -- importance weight from syllabus
  difficulty_base FLOAT DEFAULT 0.5,
  embedding_id VARCHAR,             -- Qdrant vector reference
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP
)

-- Concept Dependencies (graph edges)
concept_dependencies (
  id UUID PK,
  prerequisite_id UUID FK(concepts.id),
  dependent_id UUID FK(concepts.id),
  strength FLOAT DEFAULT 1.0        -- dependency strength 0-1
)

-- Drawing Skills
drawing_skills (
  id UUID PK,
  name VARCHAR NOT NULL,            -- e.g. "Perspective Drawing", "Composition"
  description TEXT,
  category ENUM('perspective', 'composition', 'creativity', 'proportion', 'shading', 'observation'),
  parent_id UUID FK(drawing_skills.id),
  difficulty_base FLOAT DEFAULT 0.5,
  is_active BOOLEAN DEFAULT true
)

-- Questions (Aptitude)
questions (
  id UUID PK,
  text TEXT NOT NULL,
  options JSONB NOT NULL,           -- [{id, text, is_correct}]
  correct_option_id VARCHAR NOT NULL,
  explanation TEXT NOT NULL,
  difficulty FLOAT NOT NULL,        -- 0.0 to 1.0
  source ENUM('scraped', 'generated', 'manual'),
  source_ref VARCHAR,               -- e.g. "NATA 2022 Paper 1 Q12"
  image_url VARCHAR,                -- for visual questions
  tags TEXT[],                      -- free text tags
  question_type ENUM('mcq', 'msq', 'numerical'),
  time_limit_seconds INT DEFAULT 90,
  embedding_id VARCHAR,             -- Qdrant reference for dedup
  is_active BOOLEAN DEFAULT true,
  is_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Question-Concept Mapping (many-to-many)
question_concepts (
  id UUID PK,
  question_id UUID FK(questions.id),
  concept_id UUID FK(concepts.id),
  relevance_score FLOAT DEFAULT 1.0
)

-- Drawing Tasks
drawing_tasks (
  id UUID PK,
  prompt TEXT NOT NULL,
  category ENUM('imagination', 'observation', '3d_visualization', 'memory_drawing', 'composition'),
  difficulty FLOAT NOT NULL,
  skill_ids UUID[],                 -- target skills
  reference_image_url VARCHAR,      -- optional reference
  rubric JSONB,                     -- scoring dimensions + weights
  source ENUM('generated', 'manual', 'past_paper'),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP
)

-- Practice Sessions
practice_sessions (
  id UUID PK,
  user_id UUID FK(users.id),
  mode ENUM('concept', 'adaptive', 'mock_test', 'drawing', 'mixed'),
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  total_questions INT DEFAULT 0,
  correct_count INT DEFAULT 0,
  score FLOAT DEFAULT 0.0,
  config JSONB,                     -- session configuration
  status ENUM('active', 'completed', 'abandoned') DEFAULT 'active'
)

-- Question Attempts
question_attempts (
  id UUID PK,
  user_id UUID FK(users.id),
  session_id UUID FK(practice_sessions.id),
  question_id UUID FK(questions.id),
  selected_option_id VARCHAR,
  is_correct BOOLEAN,
  time_taken_seconds INT,
  confidence_level INT,             -- 1-5 self-reported
  attempt_number INT DEFAULT 1,     -- track re-attempts
  created_at TIMESTAMP
)

-- Drawing Submissions
drawing_submissions (
  id UUID PK,
  user_id UUID FK(users.id),
  session_id UUID FK(practice_sessions.id),
  task_id UUID FK(drawing_tasks.id),
  image_url VARCHAR NOT NULL,
  submitted_at TIMESTAMP,
  time_taken_seconds INT,
  status ENUM('pending', 'evaluated', 'failed') DEFAULT 'pending'
)

-- Drawing Evaluations
drawing_evaluations (
  id UUID PK,
  submission_id UUID FK(drawing_submissions.id) UNIQUE,
  total_score FLOAT NOT NULL,       -- 0-100
  dimension_scores JSONB NOT NULL,  -- {perspective: 85, composition: 70, ...}
  feedback TEXT NOT NULL,
  improvement_suggestions JSONB,    -- [{skill, suggestion, priority}]
  raw_model_response JSONB,         -- full LLM response
  evaluated_at TIMESTAMP,
  model_version VARCHAR
)

-- User Mastery (per concept/skill)
user_mastery (
  id UUID PK,
  user_id UUID FK(users.id),
  concept_id UUID FK(concepts.id),  -- null if drawing skill
  skill_id UUID FK(drawing_skills.id), -- null if aptitude concept
  mastery_score FLOAT DEFAULT 0.0,  -- 0.0 to 1.0
  confidence FLOAT DEFAULT 0.0,
  attempt_count INT DEFAULT 0,
  correct_count INT DEFAULT 0,
  last_attempted_at TIMESTAMP,
  next_review_at TIMESTAMP,         -- spaced repetition scheduling
  streak INT DEFAULT 0,
  UNIQUE(user_id, concept_id),
  UNIQUE(user_id, skill_id)
)

-- Mistake Log (for error pattern analysis)
mistake_log (
  id UUID PK,
  user_id UUID FK(users.id),
  question_id UUID FK(questions.id),
  attempt_id UUID FK(question_attempts.id),
  error_type ENUM('conceptual', 'careless', 'time_pressure', 'unknown'),
  concept_ids UUID[],               -- which concepts were violated
  created_at TIMESTAMP
)

-- Syllabus Versions (for update tracking)
syllabus_versions (
  id UUID PK,
  version_hash VARCHAR NOT NULL,
  content JSONB NOT NULL,
  scraped_at TIMESTAMP,
  diff JSONB,                       -- diff from previous version
  is_current BOOLEAN DEFAULT false
)

-- Agent Run Logs
agent_runs (
  id UUID PK,
  agent_name VARCHAR NOT NULL,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status ENUM('running', 'completed', 'failed'),
  summary JSONB,
  error_message TEXT
)
```

---

## 5. API DESIGN

### Base URL: `/api/v1`

#### Auth
```
POST   /auth/register          Register new user
POST   /auth/login             Login, return JWT
POST   /auth/refresh           Refresh token
GET    /auth/me                Get current user profile
```

#### Questions
```
GET    /questions              List questions (with filters)
GET    /questions/{id}         Get single question
POST   /questions              Create question (admin)
PUT    /questions/{id}         Update question (admin)
GET    /questions/by-concept/{concept_id}  Questions for a concept
GET    /questions/next         Get next adaptive question for user
```

#### Practice
```
POST   /practice/sessions      Create new practice session
GET    /practice/sessions      List user sessions
GET    /practice/sessions/{id} Get session details
POST   /practice/sessions/{id}/submit  Submit answer
POST   /practice/sessions/{id}/end     End session
GET    /practice/modes         Get available modes
```

#### Drawing
```
GET    /drawing/tasks          Get drawing tasks
GET    /drawing/tasks/next     Get next adaptive drawing task
POST   /drawing/submit         Submit drawing for evaluation
GET    /drawing/submissions    List user submissions
GET    /drawing/submissions/{id}/evaluation  Get evaluation
```

#### Analytics
```
GET    /analytics/dashboard    Full dashboard summary
GET    /analytics/concepts     Concept mastery breakdown
GET    /analytics/skills       Drawing skill breakdown
GET    /analytics/predictions  Predicted NATA score
GET    /analytics/weak-areas   Top weak areas with recommendations
GET    /analytics/progress     Progress over time
```

#### Concepts
```
GET    /concepts               Full concept graph
GET    /concepts/{id}          Single concept detail
GET    /concepts/{id}/questions Questions for concept
GET    /concepts/{id}/mastery  User mastery for concept
```

#### Admin / Agents
```
POST   /admin/agents/run/{agent_name}  Trigger agent run
GET    /admin/agents/runs      Agent run history
GET    /admin/stats            Platform stats
POST   /admin/questions/verify/{id}  Verify question
```

---

## 6. AGENT WORKFLOWS

### 6.1 Syllabus Agent
```
Trigger: Celery Beat (weekly)
Flow:
  1. Fetch official NATA syllabus PDF/page
  2. Parse → structured JSON concept graph
  3. Hash content → compare with stored version
  4. If changed:
     a. Store new version with diff
     b. Create/update concept nodes
     c. Emit "syllabus_updated" event
     d. Trigger Question Gen Agent for new concepts
```

### 6.2 Question Ingestion Agent
```
Trigger: Manual / scheduled (monthly)
Flow:
  1. Scrape sources (past papers, question banks)
  2. Parse raw text → structured question format
  3. LLM tagging: assign concepts, difficulty, type
  4. Generate embeddings → check Qdrant for duplicates
  5. If unique: store in PostgreSQL + Qdrant
  6. Flag low-confidence questions for review
```

### 6.3 Question Generation Agent
```
Trigger: On demand / after syllabus update
Inputs: concept_id, difficulty, count, style
Flow:
  1. Fetch concept details + existing questions
  2. Prompt Claude: "Generate N questions for [concept] at [difficulty]"
  3. Validate: correct format, non-trivial explanation
  4. Dedup against existing bank
  5. Store as source='generated', is_verified=false
  6. Optionally: human review queue for admin
```

### 6.4 Drawing Task Generation Agent
```
Trigger: On demand / low task count detected
Flow:
  1. Sample target skills
  2. Prompt Claude: generate diverse drawing prompt
  3. Specify difficulty, category, rubric
  4. Store task with auto-generated rubric JSONB
```

### 6.5 Drawing Evaluation Agent
```
Trigger: On drawing submission
Flow:
  1. Load submission image
  2. Load task rubric
  3. Call Claude Vision with image + structured rubric prompt
  4. Parse response → dimension_scores, feedback, suggestions
  5. Store evaluation
  6. Trigger mastery update for affected skills
```

### 6.6 Adaptive Learning Agent
```
Trigger: On each question request ("next question")
Inputs: user_id, session_config
Flow:
  1. Load user mastery scores
  2. Load concept dependency graph
  3. Apply selection algorithm:
     a. Identify weakest concepts (low mastery)
     b. Check prerequisites are sufficiently mastered
     c. Select concept to target
     d. Estimate target difficulty = mastery_score + 0.1 (zone of proximal development)
  4. Select/generate question for (concept, difficulty)
  5. Return question + session metadata
Post-answer:
  1. Update mastery score (Bayesian update or ELO-style)
  2. Update next_review_at (spaced repetition: SM-2 algorithm)
  3. If error: log to mistake_log
```

### 6.7 Analytics Agent
```
Trigger: On dashboard load / periodic background refresh
Flow:
  1. Aggregate question_attempts for user
  2. Compute accuracy per concept
  3. Compute trend: 7-day rolling accuracy
  4. Identify top 5 weak concepts
  5. Predict NATA score:
     - Aptitude: weighted accuracy × 120
     - Adjust for recency and difficulty distribution
  6. Generate natural language insights via LLM
  7. Cache results (Redis, TTL=5min)
```

### 6.8 Update & Monitoring Agent
```
Trigger: Celery Beat (daily)
Flow:
  1. Check question bank size per concept → flag depleted
  2. Check last syllabus check timestamp
  3. Check drawing task variety
  4. Trigger appropriate sub-agents
  5. Log health report to agent_runs
```

---

## 7. CONCEPT GRAPH (NATA Aptitude)

```
Aptitude
├── Mathematics
│   ├── Algebra
│   │   ├── Linear Equations
│   │   ├── Quadratic Equations
│   │   └── Polynomials
│   ├── Geometry
│   │   ├── 2D Geometry (Lines, Circles, Triangles)
│   │   ├── 3D Geometry (Solids, Volumes)
│   │   └── Coordinate Geometry
│   ├── Trigonometry
│   ├── Statistics & Probability
│   └── Number Systems
├── General Aptitude
│   ├── Visual Reasoning
│   │   ├── Pattern Recognition
│   │   ├── Mirror/Water Images
│   │   ├── Embedded Figures
│   │   └── 3D Visualization
│   ├── Logical Reasoning
│   │   ├── Series Completion
│   │   ├── Analogies
│   │   └── Syllogisms
│   └── Spatial Reasoning
├── Architecture & Design GK
│   ├── Famous Architects (Indian + International)
│   ├── Architectural Movements
│   ├── Vernacular Architecture
│   ├── Sustainable Design
│   └── Building Materials
└── Physics (Applied)
    ├── Optics & Light
    ├── Forces & Structures
    └── Thermodynamics Basics

Drawing Skills
├── Perspective
│   ├── 1-Point Perspective
│   ├── 2-Point Perspective
│   └── 3-Point Perspective
├── Composition
│   ├── Rule of Thirds
│   ├── Balance & Symmetry
│   └── Focal Point
├── Proportion & Scale
├── Shading & Texture
├── Creativity & Imagination
│   ├── Memory Drawing
│   └── Conceptual Drawing
└── Observation Drawing
```

---

## 8. ADAPTIVE LEARNING ALGORITHM

### Mastery Score Update (ELO-inspired)
```python
def update_mastery(current_mastery, is_correct, question_difficulty, time_factor):
    K = 0.3  # learning rate
    expected = 1 / (1 + 10 ** ((question_difficulty - current_mastery) / 0.4))
    actual = 1.0 if is_correct else 0.0
    time_penalty = min(1.0, 1.5 - (time_taken / time_limit))
    delta = K * (actual - expected) * time_factor
    return clamp(current_mastery + delta, 0.0, 1.0)
```

### Spaced Repetition (SM-2 variant)
```
If mastery < 0.4:  review in 1 day
If mastery < 0.6:  review in 3 days
If mastery < 0.8:  review in 7 days
If mastery >= 0.8: review in 14 days
```

### Question Selection Priority
```
score = (1 - mastery) * 0.5         # Weak areas prioritized
      + (time_since_last) * 0.3     # Due for review
      + (dependency_satisfied) * 0.2 # Prerequisites met
```

---

## 9. DRAWING EVALUATION RUBRIC

Each submission is scored across 5 dimensions (total = 100):

| Dimension         | Weight | What's Evaluated                              |
|-------------------|--------|-----------------------------------------------|
| Perspective       | 25%    | Correct vanishing points, spatial depth       |
| Proportion        | 20%    | Relative scale, realistic measurements       |
| Composition       | 25%    | Layout, balance, focal point, framing         |
| Creativity        | 15%    | Originality, expressiveness, concept          |
| Execution Quality | 15%    | Line quality, shading, neatness               |

Claude Vision Prompt Template:
```
You are a NATA drawing examiner with 15 years of experience.
Evaluate this architectural drawing submission for the prompt: "{prompt}"

Score each dimension 0-100:
1. Perspective accuracy (weight: 25%)
2. Proportion and scale (weight: 20%)
3. Composition and layout (weight: 25%)
4. Creativity and interpretation (weight: 15%)
5. Execution quality (weight: 15%)

For each dimension, provide:
- Score (0-100)
- Specific observations (2-3 sentences)
- One actionable improvement suggestion

Final output: JSON format as specified.
```

---

## 10. PRACTICE MODES

| Mode            | Description                                          | Adaptive? |
|-----------------|------------------------------------------------------|-----------|
| Concept Mode    | User picks concept, gets focused questions           | No        |
| Skill Mode      | Drawing practice for a specific skill                | No        |
| Adaptive Mode   | AI selects next best question based on weak areas    | Yes       |
| Mixed Practice  | Random across all syllabus areas                     | Partial   |
| Mock Test       | 100 questions, 90 min, full NATA simulation          | No        |
| Review Mode     | Re-attempt mistakes and flagged questions            | No        |

---

## 11. PERFORMANCE TARGETS

- API response: < 200ms (p95) for core endpoints
- Drawing evaluation: < 10s
- Question generation: < 5s
- Dashboard load: < 500ms (with Redis cache)
- Database queries: < 50ms (with proper indexing)

---

## 12. IMPLEMENTATION PHASES

### Phase 1 (Foundation) — Weeks 1-3
- [ ] Backend: FastAPI app structure, DB models, auth
- [ ] Database: Schema, migrations, seed data
- [ ] Questions: CRUD, static question bank seed
- [ ] Frontend: Next.js setup, auth pages, dashboard shell
- [ ] Practice: Basic question answering, session tracking

### Phase 2 (Intelligence) — Weeks 4-6
- [ ] Adaptive engine (mastery tracking, smart question selection)
- [ ] Analytics dashboard (charts, weak area detection)
- [ ] Concept graph UI (interactive visualization)
- [ ] Spaced repetition scheduler

### Phase 3 (AI Agents) — Weeks 7-9
- [ ] Celery workers setup
- [ ] Syllabus agent
- [ ] Question ingestion agent
- [ ] Question generation agent (Claude API)
- [ ] Drawing task generation agent

### Phase 4 (Drawing) — Weeks 10-12
- [ ] Drawing task UI (canvas + upload)
- [ ] Drawing evaluation agent (Claude Vision)
- [ ] Evaluation display with feedback
- [ ] Drawing skill mastery tracking

### Phase 5 (Scale & Polish) — Weeks 13+
- [ ] Performance optimization
- [ ] Redis caching layer
- [ ] Vector DB integration (Qdrant)
- [ ] Admin panel
- [ ] Monitoring & alerting

---
