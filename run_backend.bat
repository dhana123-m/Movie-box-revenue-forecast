@echo off
setlocal
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found at backend\.venv
    echo Create it first with:
    echo   cd backend
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting Movie Box Office Revenue Forecast API...
echo   Swagger UI: http://localhost:8000/docs
echo   Health:     http://localhost:8000/api/health
echo Press Ctrl+C to stop.
echo.

".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
