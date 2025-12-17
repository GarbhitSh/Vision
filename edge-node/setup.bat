@echo off
REM Setup script for Edge Node (Windows)

echo Setting up VISION Edge Node...

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
    echo Please edit .env file with your camera settings
)

echo Setup complete!
echo To run the edge node: python app.py

