from fastapi import APIRouter, HTTPException
from ..session_store import get_or_create_engine

router = APIRouter() # Create a FastAPI router for voice-related endpoints
try:
    from ...voice.stt import SpeechToTextService
    from ...voice.tts import TextToSpeechService
    stt = SpeechToTextService()
    tts = TextToSpeechService()
    VOICE_AVAILABLE = True
except Exception:
    VOICE_AVAILABLE = False

# Endpoint to listen to the microphone, 
# transcribe the audio, and return the transcribed text as a JSON response
@router.post("/listen")
async def voice_listen(duration: int = 5):
    if not VOICE_AVAILABLE:
        raise HTTPException(503, "Voice unavailable. Install PortAudio: sudo apt install portaudio19-dev")    
    audio = stt.record(duration=duration)
    text = stt.transcribe(audio)
    return {"transcription": text}
 
# Endpoint to speak the given text using TTS (runs on the server machine) and return a confirmation response 
@router.post("/speak")
async def voice_speak(text: str):
    if not VOICE_AVAILABLE:
        raise HTTPException(503, "Voice unavailable. Install PortAudio: sudo apt install portaudio19-dev") 
    tts.speak(text)
    return {"spoken": text}