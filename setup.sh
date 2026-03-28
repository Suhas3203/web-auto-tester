#!/bin/bash
echo "============================================"
echo "  Web Auto Tester - Setup"
echo "============================================"
echo ""

echo "[1/3] Creating virtual environment..."
python -m venv .venv
source .venv/Scripts/activate

echo "[2/3] Installing dependencies..."
python -m pip install -r requirements.txt

echo "[3/3] Installing Playwright browsers..."
playwright install chromium

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  Usage:"
echo "    source .venv/Scripts/activate"
echo "    python -m web_auto_tester https://your-app.com"
echo "============================================"
