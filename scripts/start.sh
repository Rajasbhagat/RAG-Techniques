#!/bin/bash

# Determine the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting MBA Case Study Buddy..."

# 1. Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama server..."
    ollama serve > /dev/null 2>&1 &
    
    # Wait for Ollama to be ready (simple check)
    echo "Waiting for Ollama to initialize..."
    sleep 5
else
    echo "Ollama is already running."
fi

# 2. Check/Pull Model
# We assume the model is already pulled as per setup, but we can verify or just proceed.
# echo "Ensuring model deepseek-r1:8b is available..."
# ollama pull deepseek-r1:8b

# 3. Run Streamlit App
echo "Launching Streamlit App..."
cd "$PROJECT_ROOT"

# Check if venv exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found! Attempting to run with system python..."
fi

# Run the app
streamlit run app.py
