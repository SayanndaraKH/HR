@echo off
chcp 65001 >nul
title HRMS - Update from GitHub (One-Click)
cd /d "%~dp0"
color 0E

echo ================================================================
echo       ប្រព័ន្ធ HRMS - UPDATE / DEPLOY FROM GITHUB
echo ================================================================
echo.

:: 1. Pull latest code from GitHub
echo [*] កំពុងទាញយកកូដចុងក្រោយបង្អស់ពី GitHub (git pull)...
git pull origin main

if %errorlevel% neq 0 (
    color 0C
    echo [កំហុស] មិនអាចទាញយកទិន្នន័យពី GitHub បានទេ!
    pause
    exit /b 1
)

:: 2. Install / update dependencies
echo.
echo [*] កំពុងពិនិត្យ និងដំឡើងកញ្ចប់ Libraries (pip install)...
python -m pip install -r requirements.txt --quiet

:: 3. Stop running server
echo.
echo [*] កំពុងបិទ Process ចាស់...
call stop.bat >nul 2>&1

:: 4. Restart server
echo.
echo [*] កំពុងដំណើរការប្រព័ន្ធឡើងវិញ...
call run.bat

color 0A
echo.
echo ================================================================
echo   [ជោគជ័យ] ប្រព័ន្ធ HRMS ត្រូវបានធ្វើបច្ចុប្បន្នភាពរួចរាល់ជាស្ថាពរ!
echo ================================================================
pause
