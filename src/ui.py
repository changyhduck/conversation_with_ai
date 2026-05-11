from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from src.controller import AppController, AppState


class ConversationApp(tk.Tk):
    RECOMMENDED_VOICE_TUNING = {
        "silence_timeout_seconds": 1.6,
        "input_activation_rms_threshold": 500.0,
        "input_chunk_seconds": 0.1,
        "max_wait_for_speech_seconds": 12.0,
    }

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self.controller = controller
        self.title("Conversation With AI")
        self.geometry("900x620")
        self.minsize(760, 520)

        self._configure_styles()

        self.endpoint_var = tk.StringVar(value=self.controller.config.lm_studio_endpoint)
        self.microphone_var = tk.StringVar(value=self.controller.config.microphone_name)
        self.speaker_var = tk.StringVar(value=self.controller.config.speaker_name)
        self.model_var = tk.StringVar(value=self.controller.config.default_model)
        self.silence_timeout_var = tk.StringVar(value=str(self.controller.config.silence_timeout_seconds))
        self.activation_threshold_var = tk.StringVar(value=str(self.controller.config.input_activation_rms_threshold))
        self.chunk_seconds_var = tk.StringVar(value=str(self.controller.config.input_chunk_seconds))
        self.max_wait_var = tk.StringVar(value=str(self.controller.config.max_wait_for_speech_seconds))
        self.status_var = tk.StringVar(value="idle")
        self.message_var = tk.StringVar(value="Ready. Enter an LM Studio endpoint and refresh models.")

        self._build_layout()
        self._load_initial_data()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        settings_frame = ttk.LabelFrame(self, text="Settings", padding=12)
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        settings_frame.columnconfigure(0, weight=2)
        settings_frame.columnconfigure(1, weight=1)

        connection_frame = ttk.LabelFrame(settings_frame, text="Connection & Devices", padding=12)
        connection_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        connection_frame.columnconfigure(1, weight=1)
        connection_frame.columnconfigure(3, weight=1)

        tuning_frame = ttk.LabelFrame(settings_frame, text="Voice Tuning", padding=12)
        tuning_frame.grid(row=0, column=1, sticky="nsew")
        tuning_frame.columnconfigure(1, weight=1)
        tuning_frame.columnconfigure(3, weight=1)

        ttk.Label(connection_frame, text="LM Studio Endpoint").grid(row=0, column=0, sticky="w", pady=4)
        endpoint_entry = ttk.Entry(connection_frame, textvariable=self.endpoint_var)
        endpoint_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(connection_frame, text="Microphone").grid(row=1, column=0, sticky="w", pady=4)
        self.microphone_combo = ttk.Combobox(connection_frame, textvariable=self.microphone_var, state="readonly")
        self.microphone_combo.grid(row=1, column=1, sticky="ew", pady=4, padx=(0, 12))

        ttk.Label(connection_frame, text="Speaker").grid(row=1, column=2, sticky="w", pady=4)
        self.speaker_combo = ttk.Combobox(connection_frame, textvariable=self.speaker_var, state="readonly")
        self.speaker_combo.grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(connection_frame, text="Model").grid(row=2, column=0, sticky="w", pady=4)
        self.model_combo = ttk.Combobox(connection_frame, textvariable=self.model_var, state="readonly")
        self.model_combo.grid(row=2, column=1, sticky="ew", pady=4, padx=(0, 12))

        button_frame = ttk.Frame(connection_frame)
        button_frame.grid(row=2, column=2, columnspan=2, sticky="e")
        ttk.Button(button_frame, text="Refresh Devices", command=self.refresh_devices).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(button_frame, text="Refresh Models", command=self.refresh_models).grid(row=0, column=1, padx=(0, 8))

        ttk.Label(tuning_frame, text="Silence Timeout (s)").grid(row=0, column=0, sticky="w", pady=4)
        tk.Spinbox(
            tuning_frame,
            from_=0.4,
            to=5.0,
            increment=0.1,
            textvariable=self.silence_timeout_var,
            width=10,
        ).grid(row=0, column=1, sticky="ew", pady=4, padx=(0, 12))

        ttk.Label(tuning_frame, text="Activation Threshold").grid(row=0, column=2, sticky="w", pady=4)
        tk.Spinbox(
            tuning_frame,
            from_=100.0,
            to=5000.0,
            increment=50.0,
            textvariable=self.activation_threshold_var,
            width=10,
        ).grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(tuning_frame, text="Chunk Seconds").grid(row=1, column=0, sticky="w", pady=4)
        tk.Spinbox(
            tuning_frame,
            from_=0.05,
            to=0.5,
            increment=0.05,
            textvariable=self.chunk_seconds_var,
            width=10,
            format="%.2f",
        ).grid(row=1, column=1, sticky="ew", pady=4, padx=(0, 12))

        ttk.Label(tuning_frame, text="Max Wait For Speech (s)").grid(row=1, column=2, sticky="w", pady=4)
        tk.Spinbox(
            tuning_frame,
            from_=3.0,
            to=30.0,
            increment=1.0,
            textvariable=self.max_wait_var,
            width=10,
        ).grid(row=1, column=3, sticky="ew", pady=4)
        ttk.Label(
            tuning_frame,
            text="Higher silence timeout and max wait make recording more tolerant of pauses.",
            foreground="#666666",
            wraplength=320,
            justify="left",
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))

        settings_separator = ttk.Separator(settings_frame, orient="horizontal")
        settings_separator.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 8))

        action_bar = ttk.Frame(settings_frame)
        action_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        action_bar.columnconfigure(0, weight=1)

        action_hint = ttk.Label(action_bar, text="Voice tuning settings", foreground="#666666")
        action_hint.grid(row=0, column=0, sticky="w")

        action_buttons = ttk.Frame(action_bar)
        action_buttons.grid(row=0, column=1, sticky="e")
        ttk.Button(action_buttons, text="Reset", command=self.reset_voice_tuning).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(action_buttons, text="Apply", command=self.apply_settings, style="Primary.TButton").grid(row=0, column=1)

        content_frame = ttk.Frame(self, padding=(12, 6, 12, 6))
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(1, weight=1)

        ttk.Label(content_frame, text="Recognized User Text").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(content_frame, text="AI Response").grid(row=0, column=1, sticky="w", pady=(0, 6))

        self.user_text = tk.Text(content_frame, wrap="word", height=18)
        self.user_text.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        self.ai_text = tk.Text(content_frame, wrap="word", height=18, state="disabled")
        self.ai_text.grid(row=1, column=1, sticky="nsew")

        controls_frame = ttk.Frame(self, padding=(12, 0, 12, 12))
        controls_frame.grid(row=2, column=0, sticky="ew")
        controls_frame.columnconfigure(4, weight=1)

        ttk.Button(controls_frame, text="Start Listening", command=self.start_listening).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(controls_frame, text="Stop", command=self.stop_listening).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(controls_frame, text="Send Text", command=self.send_text).grid(row=0, column=2, padx=(0, 16))
        ttk.Label(controls_frame, text="Status:").grid(row=0, column=3, sticky="w")
        ttk.Label(controls_frame, textvariable=self.status_var).grid(row=0, column=4, sticky="w")

        feedback_frame = ttk.LabelFrame(self, text="Messages", padding=(12, 10))
        feedback_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 8))
        feedback_frame.columnconfigure(0, weight=1)
        ttk.Label(feedback_frame, textvariable=self.message_var, foreground="#444444", wraplength=840, justify="left").grid(
            row=0, column=0, sticky="ew"
        )

        note = (
            "This scaffold provides the UI, state management, and LM Studio wiring. "
            "Microphone capture, speech-to-text, and real speaker playback are still placeholders."
        )
        ttk.Label(self, text=note, padding=(12, 0, 12, 12), foreground="#555555").grid(row=4, column=0, sticky="w")

    def _load_initial_data(self) -> None:
        self.refresh_devices()
        self.after(150, self.refresh_models_safely)

    def refresh_devices(self) -> None:
        microphones = self.controller.list_microphones()
        speakers = self.controller.list_speakers()
        self.microphone_combo["values"] = microphones
        self.speaker_combo["values"] = speakers

        if microphones:
            self.microphone_var.set(self.controller.config.microphone_name)
        if speakers:
            self.speaker_var.set(self.controller.config.speaker_name)

    def refresh_models(self) -> None:
        try:
            self.save_settings(persist=False)
        except ValueError as exc:
            self._show_invalid_settings(exc)
            return
        self._set_status(AppState.REQUESTING_MODEL)
        try:
            models = self.controller.refresh_models()
        except Exception as exc:
            self._set_status(AppState.ERROR)
            self.message_var.set(str(exc))
            messagebox.showerror("LM Studio Error", str(exc))
            return

        self.model_combo["values"] = models
        if models:
            self.model_var.set(self.controller.config.default_model)
        self.message_var.set(f"Connected to LM Studio. Loaded {len(models)} model(s).")
        self._set_status(self.controller.state)

    def start_listening(self) -> None:
        try:
            self.save_settings(persist=False)
        except ValueError as exc:
            self._show_invalid_settings(exc)
            return
        self.controller.start_listening()
        self.message_var.set("Listening for speech. Speak a short sentence to send it through LM Studio.")
        self._set_status(self.controller.state)
        threading.Thread(target=self._run_voice_turn, daemon=True).start()

    def stop_listening(self) -> None:
        self.controller.stop_listening()
        self.message_var.set("Listening stopped.")
        self._set_status(self.controller.state)

    def send_text(self) -> None:
        try:
            self.save_settings(persist=False)
        except ValueError as exc:
            self._show_invalid_settings(exc)
            return
        user_text = self.user_text.get("1.0", tk.END)

        try:
            result = self.controller.submit_text(user_text, self.model_var.get())
        except Exception as exc:
            self._set_status(self.controller.state)
            self.message_var.set(str(exc))
            messagebox.showerror("Conversation Error", str(exc))
            return

        self._write_ai_text(result.ai_text)
        self.message_var.set("The text was sent to LM Studio and a response was returned.")
        self._set_status(self.controller.state)

    def _run_voice_turn(self) -> None:
        try:
            result = self.controller.run_voice_turn(self.model_var.get())
        except Exception as exc:
            self.after(0, self._handle_voice_turn_error, exc)
            return

        self.after(0, self._handle_voice_turn_success, result)

    def _handle_voice_turn_success(self, result) -> None:
        self.user_text.delete("1.0", tk.END)
        self.user_text.insert("1.0", result.user_text)
        self._write_ai_text(result.ai_text)
        self.message_var.set("Voice turn completed successfully.")
        self._set_status(self.controller.state)

    def _handle_voice_turn_error(self, exc: Exception) -> None:
        self._set_status(self.controller.state)
        self.message_var.set(str(exc))
        messagebox.showerror("Voice Turn Error", str(exc))

    def save_settings(self, persist: bool = True) -> None:
        silence_timeout_seconds = self._read_float(self.silence_timeout_var.get(), "Silence Timeout (s)")
        activation_threshold = self._read_float(self.activation_threshold_var.get(), "Activation Threshold")
        chunk_seconds = self._read_float(self.chunk_seconds_var.get(), "Chunk Seconds")
        max_wait_seconds = self._read_float(self.max_wait_var.get(), "Max Wait For Speech (s)")

        self.controller.save_settings(
            endpoint=self.endpoint_var.get(),
            microphone_name=self.microphone_var.get(),
            speaker_name=self.speaker_var.get(),
            default_model=self.model_var.get(),
            silence_timeout_seconds=silence_timeout_seconds,
            input_activation_rms_threshold=activation_threshold,
            input_chunk_seconds=chunk_seconds,
            max_wait_for_speech_seconds=max_wait_seconds,
        )
        self.endpoint_var.set(self.controller.config.lm_studio_endpoint)
        self.microphone_var.set(self.controller.config.microphone_name)
        self.speaker_var.set(self.controller.config.speaker_name)
        self.model_var.set(self.controller.config.default_model)
        self.silence_timeout_var.set(str(self.controller.config.silence_timeout_seconds))
        self.activation_threshold_var.set(str(self.controller.config.input_activation_rms_threshold))
        self.chunk_seconds_var.set(str(self.controller.config.input_chunk_seconds))
        self.max_wait_var.set(str(self.controller.config.max_wait_for_speech_seconds))
        if persist:
            self.message_var.set("Settings saved.")

    def apply_settings(self) -> None:
        try:
            self.save_settings(persist=True)
        except ValueError as exc:
            self._show_invalid_settings(exc)

    def reset_voice_tuning(self) -> None:
        self.silence_timeout_var.set(str(self.RECOMMENDED_VOICE_TUNING["silence_timeout_seconds"]))
        self.activation_threshold_var.set(str(self.RECOMMENDED_VOICE_TUNING["input_activation_rms_threshold"]))
        self.chunk_seconds_var.set(str(self.RECOMMENDED_VOICE_TUNING["input_chunk_seconds"]))
        self.max_wait_var.set(str(self.RECOMMENDED_VOICE_TUNING["max_wait_for_speech_seconds"]))
        self.message_var.set("Voice tuning reset to the recommended values.")

    def refresh_models_safely(self) -> None:
        try:
            self.refresh_models()
        except Exception:
            self.message_var.set(
                "Unable to auto-load models from LM Studio. Start the local server and click Refresh Models."
            )

    def _write_ai_text(self, text: str) -> None:
        self.ai_text.configure(state="normal")
        self.ai_text.delete("1.0", tk.END)
        self.ai_text.insert("1.0", text)
        self.ai_text.configure(state="disabled")

    def _set_status(self, state: AppState) -> None:
        self.status_var.set(state.value)

    def _read_float(self, value: str, label: str) -> float:
        try:
            parsed = float(value)
        except ValueError as exc:
            raise ValueError(f"{label} must be a number.") from exc

        if parsed <= 0:
            raise ValueError(f"{label} must be greater than 0.")

        return parsed

    def _show_invalid_settings(self, exc: Exception) -> None:
        self._set_status(AppState.ERROR)
        self.message_var.set(str(exc))
        messagebox.showerror("Invalid Settings", str(exc))

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        current_theme = style.theme_use()
        style.configure("Primary.TButton", padding=(12, 4), font=("Segoe UI", 9, "bold"))
        if current_theme in {"vista", "xpnative", "winnative", "clam", "alt", "default"}:
            style.map(
                "Primary.TButton",
                foreground=[("disabled", "#9a9a9a"), ("pressed", "#ffffff"), ("active", "#ffffff")],
                background=[("pressed", "#0f5a9d"), ("active", "#1f6fb2")],
            )