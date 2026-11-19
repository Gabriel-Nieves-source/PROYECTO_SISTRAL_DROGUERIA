@echo off
echo ============================================
echo   SITRAL - iniciando backend y frontend
echo ============================================

start "SITRAL - API (backend)" cmd /k "cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
start "SITRAL - Web (frontend)" cmd /k "cd frontend && python -m http.server 5500"
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5500

echo.
echo Se abrieron dos ventanas: una con la API (puerto 8000) y otra con la
echo pagina web (puerto 5500). No las cierres mientras uses el sistema.
echo.
pause
