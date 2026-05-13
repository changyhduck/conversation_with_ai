from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

try:
    import numpy as np
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    np = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - handled at runtime with a clear error.
    sd = None


@dataclass(frozen=True)
class InputDevice:
    name: str


@dataclass(frozen=True)
class CapturedAudio:
    audio_bytes: bytes
    sample_rate: int
    sample_width: int = 2


class AudioInputService:
    def list_devices(self) -> list[InputDevice]:
        if sd is None:
            return [InputDevice(name="Default microphone")]

        devices = []
        for device in sd.query_devices():
            if device.get("max_input_channels", 0) > 0:
                devices.append(InputDevice(name=device["name"]))

        return devices or [InputDevice(name="Default microphone")]

    def start_listening(self) -> None:
        self._stop_requested = False

    def stop_listening(self) -> None:
        self._stop_requested = True

    def record_utterance(
        self,
        device_name: str,
        sample_rate: int,
        silence_timeout_seconds: float,
        activation_rms_threshold: float = 500.0,
        max_wait_for_speech_seconds: float = 10.0,
        chunk_seconds: float = 0.2,
    ) -> CapturedAudio:
        if sd is None or np is None:
            raise RuntimeError("sounddevice and numpy are required for microphone capture.")

        self._stop_requested = False
        device_index = self._resolve_input_device_index(device_name)
        chunk_frames = max(1, int(sample_rate * chunk_seconds))
        collected_chunks: list[Any] = []
        started = False
        silence_elapsed = 0.0
        wait_elapsed = 0.0

        while not self._stop_requested:
            chunk = sd.rec(
                chunk_frames,
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
                device=device_index,
            )
            sd.wait()

            samples = chunk[:, 0] if getattr(chunk, "ndim", 1) > 1 else chunk
            samples = np.asarray(samples, dtype=np.int16)
            amplitude = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2))) if samples.size else 0.0

            if not started:
                wait_elapsed += chunk_seconds
                if amplitude >= activation_rms_threshold:
                    started = True
                    collected_chunks.append(samples.copy())
                    silence_elapsed = 0.0
                    continue

                if wait_elapsed >= max_wait_for_speech_seconds:
                    raise RuntimeError("No speech detected from the selected microphone.")

                continue

            collected_chunks.append(samples.copy())

            if amplitude < activation_rms_threshold:
                silence_elapsed += chunk_seconds
            else:
                silence_elapsed = 0.0

            if silence_elapsed >= silence_timeout_seconds:
                break

        if not collected_chunks:
            raise RuntimeError("Recording stopped before speech was captured.")

        audio = np.concatenate(collected_chunks).astype(np.int16)
        return CapturedAudio(audio_bytes=audio.tobytes(), sample_rate=sample_rate, sample_width=2)

    def _resolve_input_device_index(self, device_name: str) -> Optional[int]:
        if sd is None:
            return None

        if not device_name or device_name == "Default microphone":
            return None

        for index, device in enumerate(sd.query_devices()):
            if device.get("max_input_channels", 0) > 0 and device_name == device["name"]:
                return index

        return None