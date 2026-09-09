@echo off
cd /d "%~dp0"
title HRMS - Update from GitHub
python update.py
if %errorlevel% neq 0 (
    pause
)
