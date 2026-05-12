from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


@dataclass
class AppConfig:
    lm_studio_endpoint: str = "http://127.0.0.1:1234/v1"
    api_key: str = ""
    default_model: str = ""
    silence_timeout_seconds: float = 1.6
    input_activation_rms_threshold: float = 500.0
    input_chunk_seconds: float = 0.1
    max_wait_for_speech_seconds: float = 12.0
    sample_rate: int = 16000
    microphone_name: str = "Default microphone"
    speaker_name: str = "Default speaker"
    speech_language: str = "zh-TW"

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG_PATH) -> "AppConfig":
        if not path.exists():
            return cls()

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        return cls(**payload)

    def save(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(self), handle, indent=2)