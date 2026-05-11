from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.audio_input import AudioInputService
from src.audio_output import AudioOutputService
from src.config import AppConfig
from src.lm_studio_client import LMStudioClient
from src.speech_to_text import SpeechToTextService
from src.text_to_speech import TextToSpeechService


class AppState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    REQUESTING_MODEL = "requesting_model"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class ConversationResult:
    user_text: str
    ai_text: str


class AppController:
    def __init__(
        self,
        config: AppConfig,
        lm_studio_client: LMStudioClient,
        audio_input: AudioInputService,
        audio_output: AudioOutputService,
        speech_to_text: SpeechToTextService,
        text_to_speech: TextToSpeechService,
    ) -> None:
        self.config = config
        self.lm_studio_client = lm_studio_client
        self.audio_input = audio_input
        self.audio_output = audio_output
        self.speech_to_text = speech_to_text
        self.text_to_speech = text_to_speech
        self.state = AppState.IDLE
        self.available_models: list[str] = []
        self.last_error_message: str = ""

    def list_microphones(self) -> list[str]:
        devices = [device.name for device in self.audio_input.list_devices()]
        if self.config.microphone_name not in devices and devices:
            self.config.microphone_name = devices[0]
        return devices

    def list_speakers(self) -> list[str]:
        devices = [device.name for device in self.audio_output.list_devices()]
        if self.config.speaker_name not in devices and devices:
            self.config.speaker_name = devices[0]
        return devices

    def refresh_models(self) -> list[str]:
        self.state = AppState.REQUESTING_MODEL
        self.last_error_message = ""

        try:
            models = self.lm_studio_client.list_models()
            self.available_models = [model.identifier for model in models]

            if not self.available_models:
                raise ValueError("LM Studio is reachable, but no models were returned.")

            if self.config.default_model not in self.available_models:
                self.config.default_model = self.available_models[0]

            self.state = AppState.IDLE
            return self.available_models
        except Exception as exc:
            self.state = AppState.ERROR
            self.last_error_message = str(exc)
            raise

    def start_listening(self) -> None:
        self.audio_input.start_listening()
        self.last_error_message = ""
        self.state = AppState.LISTENING

    def stop_listening(self) -> None:
        self.audio_input.stop_listening()
        self.audio_output.stop()
        self.last_error_message = ""
        self.state = AppState.IDLE

    def run_voice_turn(self, model: str | None = None) -> ConversationResult:
        selected_model = model or self.config.default_model
        if not selected_model:
            raise ValueError("No model has been selected.")

        try:
            self.last_error_message = ""
            self.state = AppState.LISTENING
            captured_audio = self.audio_input.record_utterance(
                device_name=self.config.microphone_name,
                sample_rate=self.config.sample_rate,
                silence_timeout_seconds=self.config.silence_timeout_seconds,
                activation_rms_threshold=self.config.input_activation_rms_threshold,
                max_wait_for_speech_seconds=self.config.max_wait_for_speech_seconds,
                chunk_seconds=self.config.input_chunk_seconds,
            )
            self.state = AppState.TRANSCRIBING
            user_text = self.speech_to_text.transcribe(
                captured_audio.audio_bytes,
                captured_audio.sample_rate,
                captured_audio.sample_width,
            ).strip()

            if not user_text:
                raise ValueError("No speech was recognized from the recorded audio.")

            self.state = AppState.REQUESTING_MODEL
            ai_text = self.lm_studio_client.chat(user_text, selected_model)
            audio_bytes = self.text_to_speech.synthesize(ai_text)
            self.state = AppState.SPEAKING
            self.audio_output.play(audio_bytes, self.config.speaker_name)
            self.state = AppState.IDLE
            return ConversationResult(user_text=user_text, ai_text=ai_text)
        except Exception as exc:
            self.state = AppState.ERROR
            self.last_error_message = str(exc)
            raise

    def save_settings(
        self,
        endpoint: str,
        microphone_name: str,
        speaker_name: str,
        default_model: str,
        silence_timeout_seconds: float | None = None,
        input_activation_rms_threshold: float | None = None,
        input_chunk_seconds: float | None = None,
        max_wait_for_speech_seconds: float | None = None,
    ) -> None:
        self.config.lm_studio_endpoint = LMStudioClient._normalize_endpoint(endpoint).rstrip("/")
        self.config.microphone_name = microphone_name.strip() or self.config.microphone_name
        self.config.speaker_name = speaker_name.strip() or self.config.speaker_name
        self.config.default_model = default_model.strip() or self.config.default_model
        if silence_timeout_seconds is not None:
            self.config.silence_timeout_seconds = silence_timeout_seconds
        if input_activation_rms_threshold is not None:
            self.config.input_activation_rms_threshold = input_activation_rms_threshold
        if input_chunk_seconds is not None:
            self.config.input_chunk_seconds = input_chunk_seconds
        if max_wait_for_speech_seconds is not None:
            self.config.max_wait_for_speech_seconds = max_wait_for_speech_seconds
        self.lm_studio_client.endpoint = LMStudioClient._normalize_endpoint(self.config.lm_studio_endpoint)
        self.config.save()

    def submit_text(self, user_text: str, model: str | None = None) -> ConversationResult:
        normalized = user_text.strip()
        if not normalized:
            raise ValueError("User text cannot be empty.")

        selected_model = model or self.config.default_model
        if not selected_model:
            raise ValueError("No model has been selected.")

        try:
            self.last_error_message = ""
            self.state = AppState.REQUESTING_MODEL
            ai_text = self.lm_studio_client.chat(normalized, selected_model)
            audio_bytes = self.text_to_speech.synthesize(ai_text)
            self.state = AppState.SPEAKING
            self.audio_output.play(audio_bytes, self.config.speaker_name)
            self.state = AppState.IDLE
            return ConversationResult(user_text=normalized, ai_text=ai_text)
        except Exception as exc:
            self.state = AppState.ERROR
            self.last_error_message = str(exc)
            raise