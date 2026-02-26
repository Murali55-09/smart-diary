from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from tasks import celery_app, process_diary_entry

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Path to save local diary entries
ENTRY_FILE_PATH = "entries.json"

# Create an empty entries file if it doesn't exist
if not os.path.exists(ENTRY_FILE_PATH):
    with open(ENTRY_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Render the main diary page."""
    return render_template("index.html")


@app.route("/entries")
def entries():
    return render_template("entries.html")


@app.route("/chart")
def chart():
    return render_template("chart.html")


# ---------------------------------------------------------------------------
# Async upload & status polling  (Celery + Redis)
# ---------------------------------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():
    """Accept an audio file, kick off a background Celery task, and return the task ID.

    The frontend will use the returned task_id to poll /status/<task_id>.
    """
    audio = request.files.get("audio")
    language = request.form.get("language", "en")

    if not audio:
        return jsonify({"error": "No audio file provided."}), 400

    filename = secure_filename(audio.filename) or "recording.wav"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    audio.save(filepath)

    # Dispatch the heavy processing to a Celery worker
    task = process_diary_entry.delay(filepath, language)

    return jsonify({"task_id": task.id}), 202


@app.route("/status/<task_id>", methods=["GET"])
def task_status(task_id):
    """Poll the status of a background diary-processing task.

    Possible states:
        PENDING   – task is queued but not yet picked up
        TRANSCRIBING – audio is being transcribed
        ANALYSING – transcript is being summarised & analysed
        SUCCESS   – processing complete, result is attached
        FAILURE   – something went wrong
    """
    task = process_diary_entry.AsyncResult(task_id)

    if task.state == "PENDING":
        response = {"state": "PENDING", "step": "Waiting in queue..."}
    elif task.state in ("TRANSCRIBING", "ANALYSING"):
        info = task.info or {}
        response = {"state": task.state, "step": info.get("step", "")}
    elif task.state == "SUCCESS":
        response = {"state": "SUCCESS", "result": task.result}
    elif task.state == "FAILURE":
        response = {"state": "FAILURE", "step": str(task.info)}
    else:
        response = {"state": task.state, "step": "Processing..."}

    return jsonify(response)


# ---------------------------------------------------------------------------
# CRUD for diary entries (unchanged logic, cleaned up)
# ---------------------------------------------------------------------------

@app.route("/save", methods=["POST"])
def save():
    data = request.json
    date = data.get("date")
    summary = data.get("summary")
    score = data.get("score")
    emoji = data.get("emoji", "😐")

    entries = _read_entries()

    # Update if entry exists, else append
    found = False
    for entry in entries:
        if entry.get("date") == date:
            entry["summary"] = summary
            entry["score"] = score
            entry["text"] = summary
            entry["mood"] = emoji
            entry["weather"] = "Clear"
            entry["location"] = "Home"
            entry["tags"] = "voice-diary"
            entry["timestamp"] = datetime.now().isoformat()
            found = True
            break

    if not found:
        entries.append(
            {
                "date": date,
                "summary": summary,
                "score": score,
                "text": summary,
                "mood": emoji,
                "weather": "Clear",
                "location": "Home",
                "tags": "voice-diary",
                "timestamp": datetime.now().isoformat(),
            }
        )

    _write_entries(entries)
    return redirect(url_for("entries"))


@app.route("/get_entries", methods=["GET"])
def get_entries():
    entries = _read_entries()
    return jsonify(entries)


@app.route("/delete_entry", methods=["POST"])
def delete_entry():
    data = request.get_json()
    date = data.get("date")

    if not date:
        return jsonify({"status": "error", "message": "Date is required for deletion."})

    entries = _read_entries()
    entries = [entry for entry in entries if entry["date"] != date]
    _write_entries(entries)

    return jsonify({"status": "success", "message": "Entry deleted!"})


@app.route("/edit_entry", methods=["POST"])
def edit_entry():
    data = request.get_json()
    date = data.get("date")
    new_text = data.get("text")

    if not date or new_text is None:
        return jsonify({"status": "error", "message": "Date and text are required."})

    entries = _read_entries()
    found = False
    for entry in entries:
        if entry["date"] == date:
            entry["text"] = new_text
            # Keep other fields like mood/score as they were, or update if user wants
            found = True
            break
    
    if not found:
        return jsonify({"status": "error", "message": "Entry not found."})

    _write_entries(entries)
    return jsonify({"status": "success", "message": "Entry updated!"})


@app.route("/save_entry", methods=["POST"])
def save_entry():
    try:
        date = request.form.get("date")
        text = request.form.get("text")
        mood = request.form.get("mood")
        weather = request.form.get("weather")
        location = request.form.get("location")
        tags = request.form.get("tags")

        entries = _read_entries()
        entries.append(
            {
                "date": date,
                "text": text,
                "mood": mood,
                "weather": weather,
                "location": location,
                "tags": tags,
                "timestamp": datetime.now().isoformat(),
            }
        )
        _write_entries(entries)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_entries():
    """Read and return the list of diary entries from the JSON file."""
    with open(ENTRY_FILE_PATH, "r", encoding="utf-8") as f:
        try:
            entries = json.load(f)
            if not isinstance(entries, list):
                return []
            return entries
        except (ValueError, json.JSONDecodeError):
            return []


def _write_entries(entries):
    """Write the list of diary entries back to the JSON file."""
    with open(ENTRY_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=4)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
