#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
FRONTEND="$ROOT/frontend"

# ── 1. Python venv ────────────────────────────────────────────────────────────
if [ ! -d "$VENV" ]; then
  echo "[setup] creating Python venv..."
  python3 -m venv "$VENV"
fi

echo "[setup] installing Python deps..."
"$VENV/bin/pip" install -q -r "$ROOT/requirements.txt"

# ── 2. .env ───────────────────────────────────────────────────────────────────
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "[setup] created .env from .env.example — set GEMINI_API_KEY if needed"
fi

# ── 3. Frontend deps ──────────────────────────────────────────────────────────
echo "[setup] installing frontend deps..."
pnpm --dir "$FRONTEND" install --silent

# ── 4. Start backend ──────────────────────────────────────────────────────────
# Unset any shell-level API keys so .env is the single source of truth.
echo "[start] backend → http://127.0.0.1:8000  (logs → server.log)"
env -u GEMINI_API_KEY -u GOOGLE_API_KEY "$VENV/bin/python" -m src.server &
BACKEND_PID=$!

# wait for backend to be ready
for i in $(seq 1 15); do
  if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

# ── 5. Start frontend ─────────────────────────────────────────────────────────
echo "[start] frontend → http://localhost:5173"
pnpm --dir "$FRONTEND" dev &
FRONTEND_PID=$!

echo ""
echo "  meshforge is running"
echo "  Backend  : http://127.0.0.1:8000"
echo "  Frontend : http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop both servers."

# ── 6. Open browser ───────────────────────────────────────────────────────────
sleep 3
xdg-open http://localhost:5173 2>/dev/null || open http://localhost:5173 2>/dev/null || true

# ── 7. Cleanup on exit ────────────────────────────────────────────────────────
trap "echo ''; echo '[stop] shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
