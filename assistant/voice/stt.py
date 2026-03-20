from faster_whisper import WhisperModel

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except OSError:
    SOUNDDEVICE_AVAILABLE = False

# Simple speech-to-text service using the faster-whisper library
class SpeechToTextService:
    def __init__(self, model_size: str = "base") -> None:
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    # Record audio from the microphone for a given duration and sample rate 
    def record(self, duration: int = 5, sample_rate: int = 16000) -> np.ndarray:
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                "PortAudio not found. Install it with: sudo apt install portaudio19-dev"
            )
        import numpy as np
        audio = sd.rec(int(duration * sample_rate),
                       samplerate=sample_rate, channels=1, dtype="float32")
        sd.wait()
        return audio.flatten()
    
    # Transcribe the recorded audio using the Whisper model and return the transcribed text 
    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(audio, beam_size=5, language="en")
        return " ".join(s.text.strip() for s in segments)