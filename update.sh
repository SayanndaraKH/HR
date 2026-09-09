#!/usr/bin/env bash
# HRMS - Update / Deploy from GitHub (Linux / VPS)

set -e

echo "================================================================"
echo "      ប្រព័ន្ធ HRMS - UPDATE / DEPLOY FROM GITHUB"
echo "================================================================"
echo ""

echo "[*] Pulling latest code..."
git pull origin main

echo "[*] Updating Python packages..."
pip install -r requirements.txt --quiet

echo "[*] Checking database and official data..."
python -c "from app import app, db, ensure_organization_structure, ensure_default_admin; app.app_context().push(); db.create_all(); ensure_organization_structure(); ensure_default_admin(); print('Database ready.')"

echo ""
echo "================================================================"
echo "  [ជោគជ័យ] ប្រព័ន្ធ HRMS ត្រូវបាន Update រួចរាល់!"
echo "================================================================"
