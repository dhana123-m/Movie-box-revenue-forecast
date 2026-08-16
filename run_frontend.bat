@echo off
setlocal
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installing frontend dependencies (first run)...
    call npm install
)

echo Starting the Movie Box Office Revenue Forecast UI...
echo   http://localhost:5173
echo Press Ctrl+C to stop.
echo.

call npm run dev -- --port 5173 --strictPort
