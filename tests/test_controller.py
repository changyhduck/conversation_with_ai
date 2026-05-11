import unittest

from src.audio_input import AudioInputService
from src.audio_output import AudioOutputService
from src.config import AppConfig
from src.controller import AppController, AppState


class FakeLMStudioClient:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []
        self.endpoint = "http://127.0.0.1:1234/v1/"

    def list_models(self):
        return []

    def chat(self, user_message: str, model: str) -> str:
        self.messages.append((user_message, model))
        return f"echo:{user_message}"


class FakeAudioInput:
    def list_devices(self):
        return []

    def start_listening(self):
        return None

    def stop_listening(self):
        return None

    def record_utterance(
        self,
        device_name,
        sample_rate,
        silence_timeout_seconds,
        activation_rms_threshold=500.0,
        max_wait_for_speech_seconds=12.0,
        chunk_seconds=0.1,
    ):
        from src.audio_input import CapturedAudio

        return CapturedAudio(audio_bytes=b"fake-audio", sample_rate=sample_rate, sample_width=2)


class FakeSpeechToText:
    def transcribe(self, audio_bytes: bytes, sample_rate: int, sample_width: int = 2) -> str:
        return "hello from microphone"


class FakeTextToSpeech:
    def synthesize(self, text: str) -> bytes:
        return f"audio:{text}".encode("utf-8")


class FakeAudioOutput:
    def __init__(self) -> None:
        self.last_played_audio = None
        self.last_device_name = None

    def list_devices(self):
        return []

    def play(self, audio_bytes: bytes, device_name: str) -> None:
        self.last_played_audio = audio_bytes
        self.last_device_name = device_name

    def stop(self):
        self.last_played_audio = None
        self.last_device_name = None


class ControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audio_output = FakeAudioOutput()
        self.controller = AppController(
            config=AppConfig(default_model="demo-model"),
            lm_studio_client=FakeLMStudioClient(),
            audio_input=AudioInputService(),
            audio_output=self.audio_output,
            speech_to_text=FakeSpeechToText(),
            text_to_speech=FakeTextToSpeech(),
        )

    def test_submit_text_sends_message_and_returns_response(self) -> None:
        result = self.controller.submit_text("hello world")

        self.assertEqual(result.user_text, "hello world")
        self.assertEqual(result.ai_text, "echo:hello world")
        self.assertEqual(self.audio_output.last_device_name, "Default speaker")
        self.assertEqual(self.controller.state, AppState.IDLE)

    def test_submit_text_rejects_empty_input(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.submit_text("   ")

    def test_start_and_stop_listening_updates_state(self) -> None:
        self.controller.start_listening()
        self.assertEqual(self.controller.state, AppState.LISTENING)

        self.controller.stop_listening()
        self.assertEqual(self.controller.state, AppState.IDLE)

    def test_refresh_models_raises_when_no_models_are_available(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.refresh_models()

        self.assertEqual(self.controller.state, AppState.ERROR)

    def test_save_settings_normalizes_endpoint(self) -> None:
        self.controller.save_settings(
            endpoint="http://127.0.0.1:1234",
            microphone_name="Mic A",
            speaker_name="Speaker B",
            default_model="model-z",
            silence_timeout_seconds=2.1,
            input_activation_rms_threshold=750.0,
            input_chunk_seconds=0.05,
            max_wait_for_speech_seconds=14.0,
        )

        self.assertEqual(self.controller.config.lm_studio_endpoint, "http://127.0.0.1:1234/v1")
        self.assertEqual(self.controller.lm_studio_client.endpoint, "http://127.0.0.1:1234/v1/")
        self.assertEqual(self.controller.config.silence_timeout_seconds, 2.1)
        self.assertEqual(self.controller.config.input_activation_rms_threshold, 750.0)
        self.assertEqual(self.controller.config.input_chunk_seconds, 0.05)
        self.assertEqual(self.controller.config.max_wait_for_speech_seconds, 14.0)

    def test_run_voice_turn_transcribes_and_plays_response(self) -> None:
        controller = AppController(
            config=AppConfig(default_model="demo-model"),
            lm_studio_client=FakeLMStudioClient(),
            audio_input=FakeAudioInput(),
            audio_output=FakeAudioOutput(),
            speech_to_text=FakeSpeechToText(),
            text_to_speech=FakeTextToSpeech(),
        )

        result = controller.run_voice_turn()

        self.assertEqual(result.user_text, "hello from microphone")
        self.assertEqual(result.ai_text, "echo:hello from microphone")
        self.assertEqual(controller.state, AppState.IDLE)
        self.assertEqual(controller.audio_output.last_device_name, "Default speaker")


if __name__ == "__main__":
    unittest.main()