from __future__ import annotations

import os
from pathlib import Path
import tempfile

try:
    import pyttsx3
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    pyttsx3 = None


class TextToSpeechService:
    def synthesize(self, text: str) -> bytes:
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 is required for text-to-speech synthesis.")

        normalized = text.strip()
        if not normalized:
            raise ValueError("Text to synthesize cannot be empty.")

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as handle:
                temp_path = Path(handle.name)

            engine = pyttsx3.init()
            engine.save_to_file(normalized, str(temp_path))
            engine.runAndWait()

            if temp_path is None or not temp_path.exists():
                raise RuntimeError("TTS synthesis did not produce an audio file.")

            return temp_path.read_bytes()
        finally:
            if temp_path is not None and temp_path.exists():
                os.remove(temp_path)