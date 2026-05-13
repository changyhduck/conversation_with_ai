from __future__ import annotations

from collections.abc import Sequence
from typing import cast

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    sr = None


class SpeechToTextService:
    FALLBACK_LANGUAGES: Sequence[str] = ("zh-TW", "zh-CN", "en-US", "ja-JP")

    def __init__(self, language: str = "en-US") -> None:
        self.language = language

    def _candidate_languages(self) -> list[str]:
        candidates = [self.language] + list(self.FALLBACK_LANGUAGES)
        # Keep insertion order but remove duplicates.
        return list(dict.fromkeys(candidates))

    def transcribe(self, audio_bytes: bytes, sample_rate: int, sample_width: int = 2) -> str:
        if sr is None:
            raise RuntimeError("SpeechRecognition is required for transcription.")

        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio_bytes, sample_rate, sample_width)
        recognize_sphinx = getattr(recognizer, "recognize_sphinx", None)
        recognize_google = getattr(recognizer, "recognize_google", None)

        if callable(recognize_sphinx):
            try:
                return cast(str, recognize_sphinx(audio_data, language=self.language))
            except Exception:
                # Fall through to cloud STT when offline Sphinx is unavailable or failed.
                pass

        if not callable(recognize_google):
            raise RuntimeError("Speech recognition backend is unavailable.")

        for language in self._candidate_languages():
            try:
                return cast(str, recognize_google(audio_data, language=language))
            except sr.UnknownValueError:
                continue
            except sr.RequestError as exc:
                raise RuntimeError(
                    "Speech recognition request failed. Please check network connectivity."
                ) from exc

        raise RuntimeError(
            "Speech was detected but could not be understood. "
            "Try speaking slower, reducing background noise, or changing Speech Language in Settings."
        )