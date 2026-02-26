from faster_whisper import WhisperModel

# Load the faster-whisper model once when this module is imported.
# "base" is a good balance between speed and accuracy.
# compute_type="int8" reduces memory usage significantly on CPU.
model = WhisperModel("base", device="cpu", compute_type="int8")


def transcribe_audio(file_path):
    """Transcribe an audio file using faster-whisper.

    Returns the full transcribed text as a string.
    """
    segments, info = model.transcribe(file_path, beam_size=5)

    # Collect all segment texts into a single transcript string
    transcript = " ".join(segment.text.strip() for segment in segments)

    return transcript.strip()
