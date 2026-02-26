import json
import requests

# Ollama API endpoint (runs locally on default port)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


def process_text(text, language="en"):
    """Summarize, analyze sentiment, and optionally translate using Ollama.

    Sends a single prompt to the local Ollama model and parses the
    structured JSON response containing summary, sentiment, and score.

    Args:
        text: The raw transcript text to process.
        language: Target language code (e.g. "en", "hi", "es").

    Returns:
        A tuple of (summary, sentiment, score).
    """
    # Build the translation instruction if a non-English language is requested
    translation_instruction = ""
    if language and language != "en":
        translation_instruction = (
            f"\n- Translate the summary into the language with code '{language}'."
        )

    prompt = f"""You are a diary analysis assistant. Analyze the following diary transcript and respond ONLY with a valid JSON object. Do not include any other text or markdown formatting.

Instructions:
- Write a concise 2-3 sentence summary of the key thoughts and feelings expressed.
- Determine the overall emotional sentiment (e.g., Happy, Sad, Anxious, Excited, Calm, Angry, Neutral).
- Provide a corresponding emoji that best represents this emotion.
- Provide a sentiment score as a float between -1.0 (most negative) and 1.0 (most positive).{translation_instruction}

Respond with this exact JSON structure:
{{"summary": "...", "sentiment": "The Emotion Name", "emoji": "🔮", "score": 0.0}}

Diary Transcript:
\"\"\"
{text}
\"\"\"
"""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=120,
        )
        response.raise_for_status()

        result = response.json()
        raw_text = result.get("response", "")

        # Parse the JSON output from Ollama
        parsed = json.loads(raw_text)
        summary = parsed.get("summary", "Summary not available.")
        sentiment = parsed.get("sentiment", "Neutral")
        emoji = parsed.get("emoji", "😐")
        score = parsed.get("score", 0.0)

        # Clamp score to [-1, 1]
        score = max(-1.0, min(1.0, float(score)))

        return summary, sentiment, score, emoji

    except requests.exceptions.ConnectionError:
        return (
            "Error: Connection failed.",
            "Neutral",
            0.0,
            "⚠️",
        )
    except json.JSONDecodeError:
        return (
            "Error: Invalid JSON.",
            "Neutral",
            0.0,
            "❓",
        )
    except Exception as e:
        return f"Processing failed: {e}", "Neutral", 0.0