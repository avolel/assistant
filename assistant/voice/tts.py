import pyttsx3

# TextToSpeechService provides text-to-speech functionality using the pyttsx3 library.
class TextToSpeechService:
    def __init__(self, rate: int = 175, volume: float = 0.9) -> None:
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        self._engine.setProperty("volume", volume)

    # Speak the given text using the pyttsx3 engine. 
    def speak(self, text: str) -> None:
        self._engine.say(text) # Queue the text to be spoken.
        self._engine.runAndWait() # Wait for the speech to finish before returning.