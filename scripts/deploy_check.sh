#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Pre-deployment checklist — verifies all required env vars are set.
# Usage: bash scripts/deploy_check.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS=0; FAIL=0

check() {
  local name="$1"; local val="${!name:-}"
  if [ -n "$val" ]; then
    echo -e "  ${GREEN}✓${NC} $name"
    PASS=$((PASS+1))
  else
    echo -e "  ${RED}✗${NC} $name — NOT SET"
    FAIL=$((FAIL+1))
  fi
}

warn_default() {
  local name="$1"; local bad="$2"; local val="${!name:-}"
  if [ "$val" = "$bad" ]; then
    echo -e "  ${YELLOW}⚠${NC}  $name is still default '$bad' — change before production"
  fi
}

echo "ViralAI deployment checklist"
echo "────────────────────────────"

check DATABASE_URL
check DATABASE_URL_SYNC
check REDIS_URL
check ANTHROPIC_API_KEY
check APP_SECRET_KEY
check CRON_SECRET
check CORS_ORIGINS

warn_default APP_SECRET_KEY "change-me"
warn_default APP_SECRET_KEY "change-me-use-openssl-rand-hex-32"
warn_default CRON_SECRET "change-me-use-openssl-rand-hex-32"

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}All required variables set ($PASS/$((PASS+FAIL)) checks passed).${NC}"
else
  echo -e "${RED}$FAIL variable(s) missing. Fix before deploying.${NC}"
  exit 1
fi
