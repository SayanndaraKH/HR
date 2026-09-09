@echo off
chcp 65001 >nul
title HRMS - Push to GitHub (One-Click)
cd /d "%~dp0"
color 0B

echo ================================================================
echo          ប្រព័ន្ធ HRMS - PUSH UPDATE TO GITHUB
echo ================================================================
echo Repository: https://github.com/SayanndaraKH/HR
echo.

:: 1. Check if git is installed
where git >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [កំហុស / ERROR] រកមិនឃើញកម្មវិធី Git ក្នុងកុំព្យូទ័រនេះទេ!
    echo សូមដំឡើង Git ពី https://git-scm.com/downloads រួចសាកល្បងម្តងទៀត។
    echo.
    pause
    exit /b 1
)

:: 2. Check if git repository is initialized
if not exist ".git" (
    echo [*] កំពុងចាប់ផ្តើម Git Repository (git init)...
    git init -b main
    echo.
)

:: 3. Configure Git Remote Origin
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] កំពុងភ្ជាប់ទៅកាន់ GitHub Repository (https://github.com/SayanndaraKH/HR.git)...
    git remote add origin https://github.com/SayanndaraKH/HR.git
) else (
    git remote set-url origin https://github.com/SayanndaraKH/HR.git
)

:: 4. Ensure current branch is main
git branch -M main >nul 2>&1

:: 5. Show modified / new files
echo ----------------------------------------------------------------
echo បញ្ជីឯកសារដែលមានការផ្លាស់ប្តូរ (Changed Files):
echo ----------------------------------------------------------------
git status -s
echo ----------------------------------------------------------------
echo.

:: 6. Prompt for commit message
set "DEFAULT_MSG=Update HRMS System - %date% %time:~0,5%"
set /p "USER_MSG=សូមបញ្ចូលសារពិពណ៌នា (Commit Message) [ចុច ENTER យកស្វ័យប្រវត្តិ]: "

if "%USER_MSG%"=="" (
    set "COMMIT_MSG=%DEFAULT_MSG%"
) else (
    set "COMMIT_MSG=%USER_MSG%"
)

echo.
echo [*] កំពុងរៀបចំឯកសារ (git add .)...
git add .

echo [*] កំពុងកត់ត្រាការផ្លាស់ប្តូរ (git commit)...
git commit -m "%COMMIT_MSG%"

echo.
echo [*] កំពុង Push ទៅកាន់ GitHub (Branch: main)...
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo [!] ប្រព័ន្ធរកឃើញថា Remote មានឯកសារមុន កំពុងទាញយកមកបញ្ចូលគ្នា (git pull --rebase)...
    git pull --rebase origin main
    echo [*] កំពុង Push ម្តងទៀត...
    git push -u origin main
)

if %errorlevel% equ 0 (
    color 0A
    echo.
    echo ================================================================
    echo   [ជោគជ័យ / SUCCESS] ទិន្នន័យត្រូវបាន Push ទៅ GitHub រួចរាល់!
    echo   ចូលមើលកូដ៖ https://github.com/SayanndaraKH/HR
    echo ================================================================
) else (
    color 0C
    echo.
    echo ================================================================
    echo   [បរាជ័យ / FAILED] មិនអាច Push បានទេ!
    echo   សូមពិនិត្យមើលសិទ្ធិ (GitHub Authentication / Login) របស់លោកអ្នក។
    echo ================================================================
)

echo.
pause
