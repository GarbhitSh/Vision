@echo off
REM Setup script for Master Node (Windows)

echo Setting up VISION Master Node...

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Copy .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo Please edit .env file with your settings
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Initialize database
echo Initializing database...
python database\init_db.py

echo Setup complete!
echo To run the server: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

