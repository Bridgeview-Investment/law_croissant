#!/bin/bash

# RegGenome Entity Mapper - Run Script

echo "RegGenome Entity Mapper - Hack the Law Cambridge 2024"
echo "====================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model if not already installed
echo "Checking spaCy language model..."
python -m spacy download en_core_web_sm 2>/dev/null || echo "spaCy model already installed"

# Check for API key
if [ -z "$REGGENOME_API_KEY" ]; then
    if [ -f ".env" ]; then
        echo "Loading environment variables from .env file..."
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo "Warning: REGGENOME_API_KEY not set!"
        echo "Please set it in .env file or as environment variable"
    fi
fi

# Create necessary directories
mkdir -p outputs logs data/cache

# Parse command line arguments
MODE=${1:-"process"}

case $MODE in
    "process")
        echo "Running entity extraction and mapping..."
        python main.py "${@:2}"
        ;;
    
    "dashboard")
        echo "Starting interactive dashboard..."
        streamlit run streamlit_app.py
        ;;
    
    "test")
        echo "Running tests..."
        pytest tests/ -v
        ;;
    
    "demo")
        echo "Running demo with limited documents..."
        python main.py --limit 10
        ;;
    
    *)
        echo "Usage: ./run.sh [process|dashboard|test|demo]"
        echo ""
        echo "  process   - Run full entity extraction pipeline (default)"
        echo "  dashboard - Launch interactive visualization dashboard"
        echo "  test      - Run unit tests"
        echo "  demo      - Run demo with limited documents"
        exit 1
        ;;
esac