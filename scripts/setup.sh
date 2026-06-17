#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ViralAI — first-time local setup
# Usage: bash scripts/setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[setup]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $*"; }

log "ViralAI backend setup"

# 1. Python virtual environment
if [ ! -d ".venv" ]; then
  log "Creating Python virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# 2. Install dependencies
log "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 3. Environment file
if [ ! -f ".env" ]; then
  log "Creating .env from .env.example..."
  cp .env.example .env
  warn "Edit .env and set ANTHROPIC_API_KEY, DATABASE_URL, REDIS_URL, and secrets."
else
  log ".env already exists — skipping."
fi

# 4. Start infrastructure (postgres + redis) if Docker is available
if command -v docker &>/dev/null && command -v docker-compose &>/dev/null; then
  log "Starting PostgreSQL and Redis via Docker Compose..."
  docker-compose up -d postgres redis
  log "Waiting for services to be healthy..."
  sleep 5
else
  warn "Docker not found. Start PostgreSQL and Redis manually, then re-run."
fi

# 5. Run migrations
log "Running Alembic migrations..."
alembic upgrade head

# 6. Seed database (optional)
if [ -f "seeds/seed.py" ]; then
  log "Running database seeds..."
  python seeds/seed.py
fi

# 7. Dashboard dependencies
if [ -d "dashboard" ]; then
  log "Installing dashboard npm dependencies..."
  (cd dashboard && npm install --silent)
fi

log ""
log "Setup complete! Next steps:"
log "  1. Edit .env — add ANTHROPIC_API_KEY and secrets"
log "  2. Start backend:   source .venv/bin/activate && uvicorn main:app --reload"
log "  3. Start worker:    python -m arq workers.worker.WorkerSettings"
log "  4. Start dashboard: cd dashboard && npm run dev"
log "  Or run everything:  docker-compose up"
