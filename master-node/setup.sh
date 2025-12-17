#!/bin/bash
# Setup script for Master Node

echo "Setting up VISION Master Node..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your settings"
fi

# Create logs directory
mkdir -p logs

# Initialize database
echo "Initializing database..."
python database/init_db.py

echo "Setup complete!"
echo "To run the server: uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

