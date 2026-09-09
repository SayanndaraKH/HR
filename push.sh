#!/usr/bin/env bash
# HRMS - Push Update to GitHub (Linux / Mac / Bash)

set -e

REPO_URL="https://github.com/SayanndaraKH/HR.git"

echo "================================================================"
echo "          ប្រព័ន្ធ HRMS - PUSH UPDATE TO GITHUB"
echo "================================================================"
echo "Repository: $REPO_URL"
echo ""

# 1. Initialize git if needed
if [ ! -d ".git" ]; then
    echo "[*] Initializing Git..."
    git init -b main
fi

# 2. Configure remote origin
if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REPO_URL"
else
    git remote add origin "$REPO_URL"
fi

git branch -M main

# 3. Show status
echo "----------------------------------------------------------------"
echo "បញ្ជីឯកសារដែលមានការផ្លាស់ប្តូរ (Changed Files):"
echo "----------------------------------------------------------------"
git status -s
echo "----------------------------------------------------------------"
echo ""

# 4. Prompt for message
read -r -p "សូមបញ្ចូលសារពិពណ៌នា (Commit Message) [ចុច ENTER យកស្វ័យប្រវត្តិ]: " USER_MSG
if [ -z "$USER_MSG" ]; then
    COMMIT_MSG="Update HRMS System - $(date '+%Y-%m-%d %H:%M')"
else
    COMMIT_MSG="$USER_MSG"
fi

echo "[*] Staging files..."
git add .

echo "[*] Committing..."
git commit -m "$COMMIT_MSG" || echo "No changes to commit."

echo "[*] Pushing to GitHub (main)..."
if ! git push -u origin main; then
    echo "[!] Rebase with remote..."
    git pull --rebase origin main
    git push -u origin main
fi

echo ""
echo "================================================================"
echo " [ជោគជ័យ / SUCCESS] ទិន្នន័យត្រូវបាន Push ទៅ GitHub រួចរាល់!"
echo " https://github.com/SayanndaraKH/HR"
echo "================================================================"
