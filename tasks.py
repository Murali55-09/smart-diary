from celery import Celery
from speech_to_text import transcribe_audio
from summarizer import process_text

# ---------------------------------------------------------------------------
# Celery application configuration
# Uses Redis as both the message broker and the result backend.
# Make sure Redis is running on localhost:6379 before starting the worker.
# ---------------------------------------------------------------------------
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Keep results for 1 hour so the frontend can poll for them
    result_expires=3600,
)


@celery_app.task(bind=True, name="tasks.process_diary_entry")
def process_diary_entry(self, filepath, language="en"):
    """Background task: transcribe audio and analyse the transcript.

    Steps:
        1. Transcribe the audio file using faster-whisper.
        2. Send the transcript to Ollama for summarization, sentiment
           analysis, and optional translation.
        3. Return a dict with transcript, summary, sentiment, and score.
    """
    # Update task state so the frontend can show progress
    self.update_state(state="TRANSCRIBING", meta={"step": "Transcribing audio..."})

    transcript = transcribe_audio(filepath)

    if not transcript or len(transcript.split()) < 5:
        return {
            "transcript": transcript or "",
            "summary": "Text too short for meaningful sentiment analysis.",
            "sentiment": "Neutral",
            "score": 0.0,
            "emoji": "😶",
        }

    self.update_state(state="ANALYSING", meta={"step": "Analysing sentiment & summarising..."})

    summary, sentiment, score, emoji = process_text(transcript, language)

    return {
        "transcript": transcript,
        "summary": summary,
        "sentiment": sentiment,
        "score": score,
        "emoji": emoji,
    }
