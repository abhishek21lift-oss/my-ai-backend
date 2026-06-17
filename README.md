# ViralAI — AI-Powered Viral Content Creation Platform

An end-to-end production platform that uses Anthropic Claude to automatically discover viral content, analyse trends, generate hooks, write scripts, and deliver daily content recommendations for social media creators.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Next.js Dashboard (Vercel)                                         │
│  7 pages: Dashboard · Viral Feed · Trends · Research ·             │
│           Hooks · Scripts · Daily Recommendations                   │
└────────────────────────┬────────────────────────────────────────────┘
                         │ REST API (Bearer token)
┌────────────────────────▼────────────────────────────────────────────┐
│  FastAPI Backend (Render / Railway)                                 │
│  Auth · Topics · Viral Content · Trends · Research                  │
│  Hooks · Scripts · Recommendations · Agents · Cron                 │
└──────┬─────────────────────────────────────────┬────────────────────┘
       │ SQLAlchemy async                         │ ARQ jobs
┌──────▼──────────┐                    ┌──────────▼─────────┐
│ Supabase        │                    │ Redis (Upstash)    │
│ PostgreSQL 16   │                    │ Cache · Queue      │
└─────────────────┘                    └────────────────────┘
                                                 │ cron
                                       ┌─────────▼──────────┐
                                       │  ARQ Worker        │
                                       │  Daily Pipeline    │
                                       │  06:00 UTC daily   │
                                       └────────────────────┘
```

### 5-Agent AI Pipeline (Claude claude-opus-4-8)

```
Viral Scout → Trend Detector → Fitness Scientist → Hook Generator → Script Writer
     ↓               ↓                ↓                  ↓               ↓
5-7 viral items  trend score    research report      5 hooks        2 scripts
```

Every morning at **06:00 UTC** the pipeline runs automatically for all active users and topics.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, TanStack Query, Recharts |
| Backend | FastAPI 0.115, Python 3.12, SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 (Supabase) |
| Cache / Queue | Redis 7 (Upstash) via ARQ 0.26 |
| AI | Anthropic Claude claude-opus-4-8 |
| Auth | SHA-256 hashed API keys |
| Backend host | Render or Railway |
| Frontend host | Vercel |

---

## Quick Start (Local)

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker + Docker Compose (for Postgres + Redis)
- Anthropic API key

### 1. Clone and set up

```bash
git clone https://github.com/abhishek21lift-oss/my-ai-backend
cd my-ai-backend
bash scripts/setup.sh
```

The script creates `.venv`, installs dependencies, starts Docker services, runs migrations, and installs dashboard npm packages.

### 2. Configure environment

Edit `.env` — the only required change is your API key:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Run everything

**Option A — Docker Compose (recommended):**
```bash
docker-compose up
```

**Option B — individually:**
```bash
# Terminal 1: API
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Worker
source .venv/bin/activate
python -m arq workers.worker.WorkerSettings

# Terminal 3: Dashboard
cd dashboard && npm run dev
```

Open **http://localhost:3000** → enter your API key (see below) → start using the dashboard.

### 4. Create your first API key

```bash
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-key", "rate_limit_rpm": 60}'
```

Copy the returned `key` value — it starts with `sk-` and is shown **once only**.

---

## Production Deployment

### Step 1 — Supabase (Database)

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Settings → Database → Connection string**
3. Copy the **Transaction pooler** URI (port 6543)
4. Replace `postgresql://` with `postgresql+asyncpg://` (async) and `postgresql+psycopg2://` (sync)

```
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres
DATABASE_URL_SYNC=postgresql+psycopg2://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres
```

5. Run migrations against Supabase:
```bash
DATABASE_URL_SYNC="<supabase-sync-url>" alembic upgrade head
```

### Step 2 — Upstash (Redis)

1. Create a Redis database at [upstash.com](https://upstash.com)
2. Copy the **TLS connection string** (starts with `rediss://`)

```
REDIS_URL=rediss://default:[password]@[host].upstash.io:6379
```

### Step 3 — Render (Backend + Worker)

1. Connect your GitHub repo at [render.com](https://render.com)
2. Click **New → Blueprint** and select `render.yaml` from the repo root
3. Render creates two services: `viralai-api` (web) and `viralai-worker` (background worker)
4. Set these environment variables in the Render dashboard:

| Variable | Value |
|----------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `DATABASE_URL` | Supabase async URL |
| `DATABASE_URL_SYNC` | Supabase sync URL |
| `REDIS_URL` | Upstash TLS URL |
| `CORS_ORIGINS` | `https://your-dashboard.vercel.app` |

Render auto-generates `APP_SECRET_KEY` and `CRON_SECRET`.

5. Note your API URL: `https://viralai-api.onrender.com`

### Step 4 — Vercel (Dashboard)

1. Import the repo at [vercel.com](https://vercel.com)
2. Set **Root Directory** to `dashboard`
3. Set environment variables:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://viralai-api.onrender.com/api/v1` |
| `CRON_SECRET` | Same value as backend `CRON_SECRET` |

4. Deploy — Vercel automatically schedules the cron jobs defined in `vercel.json`

### Step 5 — Verify deployment

```bash
# Check backend health
curl https://viralai-api.onrender.com/health

# Check deployment variables
APP_ENV=production \
DATABASE_URL=<url> \
REDIS_URL=<url> \
ANTHROPIC_API_KEY=<key> \
CRON_SECRET=<secret> \
CORS_ORIGINS=https://your-dashboard.vercel.app \
bash scripts/deploy_check.sh
```

---

## Daily Automation

The system runs automatically every morning via two mechanisms:

### ARQ Cron (primary — runs inside the worker)

| Time (UTC) | Job | Description |
|------------|-----|-------------|
| 05:00 | `bulk_daily_reports` | Pre-generate recommendation reports |
| 06:00 | `run_daily_pipeline` | Full 5-agent pipeline for all users × topics |
| 06:00 & 18:00 | `bulk_trend_refresh` | Refresh trend data |

### Vercel Cron (backup — HTTP trigger)

| Schedule | Endpoint |
|----------|----------|
| `0 6 * * *` | `POST /api/v1/cron/daily-pipeline` |
| `0 5 * * *` | `POST /api/v1/cron/daily-reports` |

Both routes require `Authorization: Bearer <CRON_SECRET>`.

### Manual trigger

```bash
curl -X POST https://viralai-api.onrender.com/api/v1/cron/daily-pipeline \
  -H "Authorization: Bearer <CRON_SECRET>"
```

---

## API Reference

Base URL: `https://viralai-api.onrender.com/api/v1`  
Auth: `Authorization: Bearer <api-key>` on all endpoints except `/health`.

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/keys` | Create API key |
| GET | `/auth/keys` | List API keys |
| DELETE | `/auth/keys/{id}` | Revoke API key |

### Topics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/topics` | List topics |
| POST | `/topics` | Create topic |
| PUT | `/topics/{id}` | Update topic |
| DELETE | `/topics/{id}` | Delete topic |

### Viral Content
| Method | Path | Description |
|--------|------|-------------|
| GET | `/viral-content` | List (`platform`, `min_score`, `offset`, `limit`) |
| GET | `/viral-content/top` | Top items by viral score |
| POST | `/viral-content` | Create manual entry |

### Trends
| Method | Path | Description |
|--------|------|-------------|
| GET | `/trends` | List (`period`, `offset`, `limit`) |
| GET | `/trends/rising` | Rising velocity |
| GET | `/trends/viral` | Viral velocity |
| POST | `/trends/analyze` | Trigger AI analysis |

### Research, Hooks, Scripts, Recommendations
All support `GET` (list with pagination) and `POST` (create/generate).

### Agent Pipeline
| Method | Path | Description |
|--------|------|-------------|
| POST | `/agents/run` | Async pipeline (returns log ID) |
| POST | `/agents/run/sync` | Synchronous pipeline |
| GET | `/agents/run/{log_id}` | Poll status |
| GET | `/agents/logs` | Run history |

Full interactive docs: `https://viralai-api.onrender.com/docs`

---

## Project Structure

```
my-ai-backend/
├── agents/                  # 5 AI agents + orchestrator
│   ├── base.py              # ReAct loop base class
│   ├── context.py           # AgentContext / AgentResult
│   ├── viral_scout/
│   ├── trend_detector/
│   ├── fitness_scientist/
│   ├── hook_generator/
│   ├── script_writer/
│   └── orchestrator/        # Pipeline coordination
├── core/                    # Config, DB, Redis, auth
├── dashboard/               # Next.js 14 frontend
│   └── src/
│       ├── app/             # App Router pages
│       ├── components/      # UI, shared, charts, layout
│       ├── hooks/           # TanStack Query hooks
│       └── lib/             # API client, types, utils
├── migrations/              # Alembic migrations
├── models/                  # SQLAlchemy ORM + Pydantic schemas
├── repositories/            # Data access layer (12 repos)
├── routes/                  # FastAPI routers
├── scripts/                 # Setup + deploy scripts
├── seeds/                   # Database seed data
├── services/                # Business logic + LLM services
├── workers/                 # ARQ worker + task definitions
│   └── tasks/
│       ├── agent_workflow.py
│       ├── daily_pipeline.py   # Morning automation
│       ├── daily_report.py
│       └── ...
├── Dockerfile
├── docker-compose.yml
├── render.yaml              # Render.com blueprint
└── requirements.txt
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_ENV` | Yes | `development` or `production` |
| `APP_SECRET_KEY` | Yes | Random 32-byte hex secret |
| `DATABASE_URL` | Yes | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `DATABASE_URL_SYNC` | Yes | Sync PostgreSQL URL (`postgresql+psycopg2://...`) |
| `REDIS_URL` | Yes | Redis URL (`redis://` or `rediss://` for TLS) |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key (`sk-ant-api03-...`) |
| `CRON_SECRET` | Yes (prod) | Protects HTTP cron endpoints |
| `CORS_ORIGINS` | Yes (prod) | Comma-separated allowed origins |
| `DB_POOL_SIZE` | No | Connection pool size (default: 5) |
| `DB_MAX_OVERFLOW` | No | Max overflow connections (default: 10) |
| `DB_POOL_RECYCLE` | No | Connection recycle seconds (default: 300) |

---

## QA Checklist

- [x] All 10 database tables created via Alembic migrations
- [x] API key auth with SHA-256 hashing and constant-time comparison
- [x] Rate limiting via Redis sliding window per API key
- [x] 5-agent ReAct pipeline with independent per-stage logging
- [x] Pipeline partial-failure recovery (each stage commits independently)
- [x] ARQ background jobs with 10-minute timeout
- [x] Daily cron: 06:00 UTC full pipeline + 05:00 UTC recommendations
- [x] HTTP cron endpoints protected by CRON_SECRET
- [x] CORS configured from environment variable
- [x] Structured JSON logging with ctx_ prefix convention
- [x] All 7 dashboard pages connected to real API data
- [x] Pipeline modal with live stage tracking (3s polling)
- [x] Loading skeletons and empty states on all pages
- [x] Pagination on all list pages
- [x] Responsive design with mobile sidebar drawer
- [x] API key stored in localStorage, never logged
- [x] Vercel cron schedules in `vercel.json`
- [x] Render deployment blueprint in `render.yaml`
- [x] Docker Compose for full local stack
- [x] `.gitignore` covering all build artifacts and secrets
