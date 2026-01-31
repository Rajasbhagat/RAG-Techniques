# Resource Management Protocol

This document outlines the procedures for starting and stopping the MBA Case Study Buddy application to manage system resources effectively.

## 🛑 Stopping the Application (Save Resources)

To completely shut down the application and release resources (including the Ollama AI model):

1.  Open your terminal.
2.  Navigate to the project directory:
    ```bash
    cd /Users/rajas/Desktop/AntiGravity/RAG/reference_repo/mba_case_study_buddy
    ```
3.  Run the stop script:
    ```bash
    ./scripts/stop.sh
    ```

**What this does:**
-   Terminates the Streamlit web server.
-   Terminates the Ollama model server (releasing RAM/VRAM).

---

## 🚀 Restarting the Application

To start the application again when you are ready to work:

1.  Open your terminal.
2.  Navigate to the project directory:
    ```bash
    cd /Users/rajas/Desktop/AntiGravity/RAG/reference_repo/mba_case_study_buddy
    ```
3.  Run the start script:
    ```bash
    ./scripts/start.sh
    ```

**What this does:**
-   Checks if Ollama is running, and starts it if needed.
-   Activates the virtual environment.
-   Launches the Streamlit app.
-   The app will be available at: [http://localhost:8501](http://localhost:8501)
