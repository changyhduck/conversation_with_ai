# Conversation With AI

## Project Status

This repository now contains a working Python desktop skeleton with a runnable UI, controller logic, LM Studio client wiring, real microphone capture, speech-to-text, text-to-speech, and playback support.

The current implementation is still an MVP, but the main conversation loop is now connected end to end.

The purpose of this file is to define a clear implementation target for a desktop application that:

1. Listens to the user's speech.
2. Converts speech to text.
3. Sends the text to an AI model hosted by LM Studio.
4. Converts the AI response to speech.
5. Plays the response through the selected speaker.

## Goal

Build a Python desktop application for hands-free voice conversation with a local AI model through the LM Studio API.

## Target User Flow

1. The user opens the application.
2. The user selects a microphone.
3. The user selects a speaker.
4. The user enters the LM Studio server URL if needed.
5. The application loads the available models from LM Studio.
6. The user selects a model.
7. The application listens for speech.
8. When speech is detected, the application records until silence is detected.
9. The application converts the audio to text.
10. The application sends the text to the selected AI model.
11. The application converts the AI response to speech.
12. The application plays the response.
13. If the user starts speaking again, playback stops and a new interaction begins.

## Functional Requirements

### Audio Input

1. The application must list available microphones.
2. The user must be able to select one microphone.
3. The application must detect when the user starts speaking.
4. The application must stop recording after a configurable period of silence.

### Speech to Text

1. Recorded audio must be converted to text.
2. If speech recognition fails, the application must show an error and allow retry.

### LM Studio Integration

1. The application must connect to a running LM Studio server.
2. The application must fetch the list of available models.
3. The user must be able to select one model.
4. The application must send the recognized text to the selected model.
5. The application must display the AI response as text.

### Text to Speech

1. The AI response must be converted to audio.
2. The application must list available speakers or output devices.
3. The user must be able to select one speaker.
4. Playback must stop if the user starts speaking again.

### User Interface

The UI should provide at least the following controls and status areas:

1. Microphone selector.
2. Speaker selector.
3. LM Studio endpoint input.
4. Model selector.
5. Start and stop listening control.
6. Status area for states such as idle, listening, transcribing, thinking, and speaking.
7. Text area for recognized user input.
8. Text area for AI output.
9. Error message area.

## Non-Functional Requirements

1. The application should run on Windows first.
2. Python 3.10 or above is recommended.
3. The UI should remain responsive while recording, calling the model, and playing audio.
4. Temporary audio files should be cleaned up automatically if file-based text-to-speech is used.
5. Network and device errors should be handled gracefully.

## Recommended Technical Design

### Suggested Stack

1. Python for the main application.
2. Tkinter or PySide6 for the desktop UI.
3. sounddevice or PyAudio for microphone capture.
4. faster-whisper, SpeechRecognition, or another speech-to-text solution.
5. requests for LM Studio API calls.
6. pyttsx3, edge-tts, or gTTS for text-to-speech.
7. simpleaudio, pygame, or another reliable playback library.

### Suggested Modules

1. ui: desktop interface and user interactions.
2. audio_input: microphone discovery, recording, silence detection.
3. speech_to_text: transcription logic.
4. lm_studio_client: model listing and chat completion requests.
5. text_to_speech: audio generation from text.
6. audio_output: speaker discovery and playback.
7. controller: state machine that coordinates the full conversation loop.
8. config: settings such as endpoint, thresholds, and default device IDs.

### Suggested Project Structure

```text
conversation_with_ai/
|- Main.md
|- requirements.txt
|- app.py
|- src/
|  |- ui.py
|  |- controller.py
|  |- config.py
|  |- audio_input.py
|  |- audio_output.py
|  |- speech_to_text.py
|  |- text_to_speech.py
|  |- lm_studio_client.py
|- tests/
|  |- test_lm_studio_client.py
|  |- test_controller.py
```

## LM Studio Assumptions

This project assumes:

1. LM Studio is already installed and running locally.
2. Its local server endpoint is enabled.
3. At least one compatible model is loaded or available.

The document should avoid claiming that an API key is always required. Many LM Studio local server setups use a local endpoint without authentication. The implementation should make endpoint and optional API key configurable.

## State Machine

The application should behave roughly as follows:

1. idle
2. listening
3. recording
4. transcribing
5. requesting_model
6. speaking
7. error

Transitions should be explicit so that playback interruption and recovery are predictable.

## Error Cases To Handle

1. No microphone detected.
2. No speaker detected.
3. LM Studio server is not reachable.
4. No model is available.
5. Speech recognition returns empty text.
6. Text-to-speech generation fails.
7. Audio playback device becomes unavailable.

## Minimum Viable Product

The first working version should support:

1. Manual microphone selection.
2. Manual speaker selection.
3. Manual model selection.
4. Push-to-talk or basic auto-recording.
5. Speech-to-text for a single utterance.
6. LM Studio text response.
7. Text-to-speech playback.

Auto interruption of playback by new speech can be implemented after the basic loop works reliably.

## Implementation Plan

1. Create the base project structure.
2. Implement LM Studio connection and model listing first.
3. Implement speech-to-text with a fixed audio input flow.
4. Implement text-to-speech and speaker playback.
5. Build the UI around the working backend modules.
6. Add silence detection and automatic interruption.
7. Add tests for controller logic and LM Studio client behavior.

## Validation Checklist

The project can be considered working when all of the following are true:

1. The application starts without crashing.
2. The microphone list is shown.
3. The speaker list is shown.
4. LM Studio models can be loaded successfully.
5. A spoken sentence is transcribed correctly.
6. The transcribed sentence is sent to the selected model.
7. The model response is displayed in the UI.
8. The response is spoken through the selected speaker.
9. Common failure cases show clear error messages.

## Run Instructions

These commands are the intended future workflow after code is added:

```bash
pip install -r requirements.txt
pyright
python app.py
```

The initial skeleton for these files now exists in this repository.

## Notes For Implementation

1. The current repository already includes a runnable UI and a real audio pipeline, so the next step should focus on improving robustness, error handling, and voice activity tuning.
2. Keep audio input, AI request, and audio output logic separated. This makes testing and future backend swaps easier.
3. Avoid hard-coding LM Studio settings.
4. Prefer configuration values for silence timeout, sample rate, and model endpoint.
5. The UI still runs the voice turn in a background thread so the window stays responsive during recording and playback.
