from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
import tempfile

try:
    import numpy as np
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    np = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    sd = None

try:
    import soundfile as sf
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    sf = None

try:
    import winsound
except ImportError:  # pragma: no cover - Windows-only fallback.
    winsound = None


@dataclass(frozen=True)
class OutputDevice:
    name: str


class AudioOutputService:
    def __init__(self) -> None:
        self.last_played_audio: bytes | None = None
        self.last_device_name: str | None = None

    def list_devices(self) -> list[OutputDevice]:
        if sd is None:
            return [OutputDevice(name="Default speaker")]

        devices = []
        for device in sd.query_devices():
            if device.get("max_output_channels", 0) > 0:
                devices.append(OutputDevice(name=device["name"]))

        return devices or [OutputDevice(name="Default speaker")]

    def play(self, audio_bytes: bytes, device_name: str) -> None:
        if sd is None or sf is None or np is None:
            self._play_with_winsound_fallback(audio_bytes)
            self.last_played_audio = audio_bytes
            self.last_device_name = device_name
            return

        try:
            with io.BytesIO(audio_bytes) as buffer:
                data, sample_rate = sf.read(buffer, dtype="float32", always_2d=True)

            device_index = self._resolve_output_device_index(device_name)
            self.last_played_audio = audio_bytes
            self.last_device_name = device_name
            sd.play(data, samplerate=sample_rate, device=device_index)
            sd.wait()
        except Exception:
            self._play_with_winsound_fallback(audio_bytes)
            self.last_played_audio = audio_bytes
            self.last_device_name = device_name

    def stop(self) -> None:
        if sd is not None:
            sd.stop()
        self.last_played_audio = None
        self.last_device_name = None

    def _resolve_output_device_index(self, device_name: str) -> int | None:
        if sd is None:
            return None

        if not device_name or device_name == "Default speaker":
            return None

        for index, device in enumerate(sd.query_devices()):
            if device.get("max_output_channels", 0) > 0 and device_name == device["name"]:
                return index

        return None

    def _play_with_winsound_fallback(self, audio_bytes: bytes) -> None:
        if winsound is None:
            raise RuntimeError("No supported audio playback backend is available.")

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as handle:
                temp_path = Path(handle.name)
                handle.write(audio_bytes)
                handle.flush()

            filename_flag = getattr(winsound, "SND_FILENAME", 0)
            sync_flag = getattr(winsound, "SND_SYNC", 0)
            winsound.PlaySound(str(temp_path), filename_flag | sync_flag)
        finally:
            if temp_path is not None and temp_path.exists():
                os.remove(temp_path)