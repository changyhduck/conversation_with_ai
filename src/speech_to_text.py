from __future__ import annotations

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    sr = None


class SpeechToTextService:
    def __init__(self, language: str = "en-US") -> None:
        self.language = language

    def transcribe(self, audio_bytes: bytes, sample_rate: int, sample_width: int = 2) -> str:
        if sr is None:
            raise RuntimeError("SpeechRecognition is required for transcription.")

        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio_bytes, sample_rate, sample_width)

        try:
            return recognizer.recognize_sphinx(audio_data, language=self.language)
        except Exception:
            try:
                return recognizer.recognize_google(audio_data, language=self.language)
            except sr.UnknownValueError as exc:
                raise RuntimeError("Speech was detected but could not be understood.") from exc
            except sr.RequestError as exc:
                raise RuntimeError("Speech recognition request failed.") from exc