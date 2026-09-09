@echo off
cd /d "%~dp0"

:: Stop process on port 5000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

ping 127.0.0.1 -n 2 >nul
exit
