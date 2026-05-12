from src.audio_input import AudioInputService
from src.audio_output import AudioOutputService
from src.config import AppConfig
from src.controller import AppController
from src.lm_studio_client import LMStudioClient
from src.speech_to_text import SpeechToTextService
from src.text_to_speech import TextToSpeechService
from src.ui import ConversationApp


def main() -> None:
    config = AppConfig.load()
    client = LMStudioClient(endpoint=config.lm_studio_endpoint, api_key=config.api_key)
    controller = AppController(
        config=config,
        lm_studio_client=client,
        audio_input=AudioInputService(),
        audio_output=AudioOutputService(),
        speech_to_text=SpeechToTextService(language=config.speech_language),
        text_to_speech=TextToSpeechService(),
    )
    app = ConversationApp(controller)
    app.mainloop()


if __name__ == "__main__":
    main()