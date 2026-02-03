@echo off
REM MedShare Quick Setup Script

echo.
echo ========================================
echo  MedShare - Medicine Donation Platform
echo  Setup & Run Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [2/4] Running migrations...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Failed to run migrations
    pause
    exit /b 1
)

echo.
echo [3/4] Creating media folders...
if not exist "media\medicines" mkdir media\medicines
if not exist "media\profiles" mkdir media\profiles
echo Media folders ready!

echo.
echo [4/4] Populating test data...
python manage.py populate_data

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Starting Django Development Server...
echo Visit: http://127.0.0.1:8000/
echo.
echo Test Accounts:
echo   Donor: donor1 / donor123
echo   NGO: ngo1 / ngo123
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python manage.py runserver
