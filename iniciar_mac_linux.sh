#!/usr/bin/env bash
# SITRAL — inicia el backend (API) y el frontend (web) a la vez.
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  SITRAL - iniciando backend y frontend"
echo "============================================"

(cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

sleep 3

(cd frontend && python3 -m http.server 5500) &
FRONTEND_PID=$!

sleep 2
URL="http://127.0.0.1:5500"
if command -v open >/dev/null 2>&1; then open "$URL"; fi
if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"; fi

echo ""
echo "API en http://127.0.0.1:8000  |  Web en $URL"
echo "Presiona Ctrl+C para detener ambos servidores."
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
