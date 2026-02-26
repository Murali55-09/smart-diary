# Dilse.ai - Voice Journal with AI Insights

Dilse.ai is a premium, AI-powered voice diary that transcribes your reflections, summarizes your thoughts, and analyzes your emotional journey. It uses local AI models for maximum privacy and performance.

## Prerequisites

To run this project, you need the following installed on your laptop:

1. **Python 3.8+**
2. **Ollama**: Download and install from [ollama.com](https://ollama.com/).
3. **Redis**: Needed for the background task processing.
   - **Windows**: Install via [memurai](https://www.memurai.com/get-memurai) or [Redis on WSL2](https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-database#install-redis).
   - **Mac/Linux**: `brew install redis` or `sudo apt install redis-server`.

## Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Dilse.2
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Pull the AI model**:
   Ollama needs the specific model used for analysis. Run:
   ```bash
   ollama pull llama3.2
   ```

## How to Run

You need to run **three things** simultaneously:

1. **Start Redis Server**:
   Ensure your Redis server is running (usually on port 6379).

2. **Start the Celery Worker**:
   This handles the transcription and AI analysis in the background.
   ```bash
   celery -A tasks worker --loglevel=info -P solo
   ```
   *(Note: `-P solo` is recommended for Windows users)*

3. **Start the Flask Web App**:
   ```bash
   python app.py
   ```

Now open [http://127.0.0.1:5001](http://127.0.0.1:5001) in your browser.

## Tech Stack
- **Frontend**: Vanilla HTML/CSS/JS with "Speak Your Story" premium aesthetic.
- **Backend**: Flask (Python).
- **Speech-to-Text**: `faster-whisper`.
- **LLM/Analysis**: Ollama (`llama3.2`).
- **Async Tasks**: Celery + Redis.
