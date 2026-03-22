# Voice routes: record + transcribe audio (listen) and synthesise speech (speak).
# Voice dependencies (faster-whisper, sounddevice, pyttsx3) require native system libraries
# that may not be installed. The try/except at import time gracefully degrades —
# the endpoints still exist but return 503 if the dependencies are missing.
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from ..session_store import get_or_create_engine

router = APIRouter()

# Attempt to import voice services. If PortAudio or faster-whisper isn't installed,
# the import raises an OSError. We catch it and flag the services as unavailable
# rather than crashing the whole server at startup.
try:
    from ...voice.stt import SpeechToTextService
    from ...voice.tts import TextToSpeechService
    stt             = SpeechToTextService()
    tts             = TextToSpeechService()
    VOICE_AVAILABLE = True
except Exception as e:
    print(f"Voice unavailable: {type(e).__name__}: {e}")
    VOICE_AVAILABLE = False


@router.post("/listen")
async def voice_listen(duration: int = 5):
    """Record `duration` seconds of audio from the microphone, transcribe it, and return the text.
    `duration` is a query parameter: POST /api/voice/listen?duration=10"""
    if not VOICE_AVAILABLE:
        raise HTTPException(503, "Voice unavailable. Install PortAudio: sudo apt install portaudio19-dev")
    audio = stt.record(duration=duration)
    text  = stt.transcribe(audio)
    return {"transcription": text}


@router.post("/transcribe")
async def voice_transcribe(audio: UploadFile = File(...)):
    """Accept an audio file upload from the browser (WebM/Ogg/WAV) and return its transcription.
    This lets the browser record audio client-side and only send the finished clip."""
    if not VOICE_AVAILABLE:
        raise HTTPException(503, "Voice unavailable. Install PortAudio: sudo apt install portaudio19-dev")
    audio_bytes = await audio.read()
    # Infer file extension from the uploaded filename for temp file suffix.
    import os
    suffix = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
    text = stt.transcribe_file(audio_bytes, suffix=suffix)
    return {"transcription": text}


@router.post("/speak")
async def voice_speak(text: str):
    """Synthesise speech for `text` and return WAV audio bytes.
    The browser can play the returned audio/wav blob directly."""
    if not VOICE_AVAILABLE:
        raise HTTPException(503, "Voice unavailable. Install PortAudio: sudo apt install portaudio19-dev")
    audio_bytes = tts.speak_to_bytes(text)
    return Response(content=audio_bytes, media_type="audio/wav")