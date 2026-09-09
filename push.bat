@echo off
cd /d "%~dp0"
title HRMS - Push to GitHub
python push.py
if %errorlevel% neq 0 (
    pause
)
