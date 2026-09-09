@echo off
cd /d "%~dp0"

:: 1. Stop any old process on port 5000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Ensure database is seeded
python seed_data.py >nul 2>&1

:: 3. Start server in background with pythonw (No CMD window stays open)
start "" pythonw app.py

:: 4. Wait 2 seconds
ping 127.0.0.1 -n 3 >nul

:: 5. Open Web Browser automatically
start "" "http://127.0.0.1:5000/"

:: 6. Close CMD window immediately
exit
