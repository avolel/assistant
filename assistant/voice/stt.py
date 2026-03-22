# Speech-to-text using faster-whisper, a faster reimplementation of OpenAI's Whisper model.
# Runs fully locally on CPU (int8 quantisation) or GPU.
# sounddevice requires PortAudio to be installed on the system (sudo apt install portaudio19-dev).
from faster_whisper import WhisperModel
import numpy as np

# Attempt to import sounddevice at module load time.
# If PortAudio is missing, it raises OSError — we catch it and flag as unavailable
# so the rest of the server can still start without voice support.
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except OSError:
    SOUNDDEVICE_AVAILABLE = False


class SpeechToTextService:
    def __init__(self, model_size: str = "base") -> None:
        # Load the Whisper model onto CPU with int8 quantisation (smaller, faster, lower memory use).
        # model_size options: tiny / base / small / medium / large — bigger = more accurate but slower.
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def record(self, duration: int = 5, sample_rate: int = 16000) -> np.ndarray:
        """Record `duration` seconds of mono audio from the default microphone.
        Returns a 1D float32 numpy array of audio samples at 16kHz (what Whisper expects)."""
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                "PortAudio not found. Install it with: sudo apt install portaudio19-dev"
            )
        # sd.rec() starts recording non-blockingly. sd.wait() blocks until it finishes.
        audio = sd.rec(int(duration * sample_rate),
                       samplerate=sample_rate, channels=1, dtype="float32")
        sd.wait()
        return audio.flatten()   # .flatten() collapses shape (N, 1) to (N,) — 1D array

    def transcribe(self, audio: np.ndarray) -> str:
        """Run Whisper inference on the audio array and return the transcribed text.
        beam_size=5 balances accuracy vs. speed. language="en" skips language detection."""
        segments, _ = self.model.transcribe(audio, beam_size=5, language="en")
        # segments is a generator of Segment objects. Join their text with spaces.
        return " ".join(s.text.strip() for s in segments)