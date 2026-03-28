@echo off
echo ============================================
echo   Web Auto Tester - Setup
echo ============================================
echo.

echo [1/3] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/3] Installing dependencies...
pip install -r requirements.txt

echo [3/3] Installing Playwright browsers...
playwright install chromium

echo.
echo ============================================
echo   Setup complete!
echo.
echo   Usage:
echo     venv\Scripts\activate.bat
echo     python -m web_auto_tester https://your-app.com
echo ============================================
