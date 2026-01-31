#!/bin/bash

echo "🛑 Stopping MBA Case Study Buddy..."

# Stop Streamlit
if pgrep -f "streamlit run app.py" > /dev/null; then
    echo "Terminating Streamlit app..."
    pkill -f "streamlit run app.py"
else
    echo "Streamlit app not found running."
fi

# Stop Ollama
if pgrep -x "ollama" > /dev/null; then
    echo "Terminating Ollama server..."
    # Try to stop gently first, though pkill is often SIGTERM which is gentle.
    pkill -x "ollama"
else
    echo "Ollama server not found running."
fi

echo "✅ Project shut down successfully. Resources released."
