# Text-to-speech using pyttsx3, which wraps the OS's native speech engine.
# On Linux it uses espeak; on macOS it uses NSSpeechSynthesizer; on Windows it uses SAPI.
# No internet connection required — fully offline.
import pyttsx3


class TextToSpeechService:
    def __init__(self, rate: int = 175, volume: float = 0.9) -> None:
        # pyttsx3.init() creates the speech engine and connects to the OS TTS backend.
        self._engine = pyttsx3.init()
        # `rate` is words per minute; 175 is roughly normal conversational speed.
        self._engine.setProperty("rate", rate)
        # `volume` is 0.0 (silent) to 1.0 (full). 0.9 gives a slight headroom buffer.
        self._engine.setProperty("volume", volume)

    def speak(self, text: str) -> None:
        """Queue text for synthesis and block until the audio finishes playing.
        say() adds to an internal queue; runAndWait() processes it and returns when done."""
        self._engine.say(text)
        self._engine.runAndWait()