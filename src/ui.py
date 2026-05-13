from __future__ import annotations

import re
import threading
import tkinter as tk
import webbrowser
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from src.controller import AppController, AppState, ConversationResult


class ConversationApp(tk.Tk):
    RECOMMENDED_VOICE_TUNING = {
        "silence_timeout_seconds": 1.6,
        "input_activation_rms_threshold": 500.0,
        "input_chunk_seconds": 0.1,
        "max_wait_for_speech_seconds": 12.0,
    }
    INLINE_MARKDOWN_PATTERN = re.compile(
        r"(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))"
    )
    MAX_TABLE_COLUMN_WIDTH = 36

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
        self.speech_language_var = tk.StringVar(value=self.controller.config.speech_language)
        self.silence_timeout_var = tk.StringVar(value=str(self.controller.config.silence_timeout_seconds))
        self.activation_threshold_var = tk.StringVar(value=str(self.controller.config.input_activation_rms_threshold))
        self.chunk_seconds_var = tk.StringVar(value=str(self.controller.config.input_chunk_seconds))
        self.max_wait_var = tk.StringVar(value=str(self.controller.config.max_wait_for_speech_seconds))
        self.status_var = tk.StringVar(value="idle")
        self.message_var = tk.StringVar(value="Ready. Enter an LM Studio endpoint and refresh models.")
        self._link_tag_counter = 0
        self._message_before_link_preview: str | None = None

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

        ttk.Label(connection_frame, text="Speech Language").grid(row=2, column=2, sticky="w", pady=4)
        self.language_combo = ttk.Combobox(
            connection_frame,
            textvariable=self.speech_language_var,
            values=["en-US", "zh-TW", "zh-CN", "ja-JP"],
            state="readonly",
        )
        self.language_combo.grid(row=2, column=3, sticky="ew", pady=4)
        self.language_combo.bind("<<ComboboxSelected>>", lambda e: self._on_language_changed())

        button_frame = ttk.Frame(connection_frame)
        button_frame.grid(row=3, column=0, columnspan=4, sticky="e")
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
        self._configure_ai_markdown_tags()

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

    def _handle_voice_turn_success(self, result: ConversationResult) -> None:
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
            speech_language=self.speech_language_var.get(),
        )
        self.endpoint_var.set(self.controller.config.lm_studio_endpoint)
        self.microphone_var.set(self.controller.config.microphone_name)
        self.speaker_var.set(self.controller.config.speaker_name)
        self.model_var.set(self.controller.config.default_model)
        self.speech_language_var.set(self.controller.config.speech_language)
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

    def _on_language_changed(self) -> None:
        try:
            language = self.speech_language_var.get()
            self.controller.save_settings(
                endpoint=self.endpoint_var.get(),
                microphone_name=self.microphone_var.get(),
                speaker_name=self.speaker_var.get(),
                default_model=self.model_var.get(),
                speech_language=language,
            )
            self.message_var.set(f"Speech language changed to {language}.")
        except Exception as exc:
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
        self._message_before_link_preview = None
        for tag_name in self.ai_text.tag_names():
            if tag_name.startswith("md_link_"):
                self.ai_text.tag_delete(tag_name)
        self._link_tag_counter = 0
        self._render_markdown_to_ai_text(text)
        self.ai_text.configure(state="disabled")

    def _configure_ai_markdown_tags(self) -> None:
        base_font = tkfont.nametofont("TkDefaultFont")
        mono_font = tkfont.nametofont("TkFixedFont")

        heading1_font = base_font.copy()
        heading1_font.configure(size=max(base_font.cget("size") + 5, 14), weight="bold")
        heading2_font = base_font.copy()
        heading2_font.configure(size=max(base_font.cget("size") + 3, 12), weight="bold")
        heading3_font = base_font.copy()
        heading3_font.configure(size=max(base_font.cget("size") + 1, 11), weight="bold")
        bold_font = base_font.copy()
        bold_font.configure(weight="bold")
        italic_font = base_font.copy()
        italic_font.configure(slant="italic")

        self.ai_text.tag_configure("md_p", spacing1=2, spacing3=4)
        self.ai_text.tag_configure("md_h1", font=heading1_font, spacing1=8, spacing3=6)
        self.ai_text.tag_configure("md_h2", font=heading2_font, spacing1=6, spacing3=4)
        self.ai_text.tag_configure("md_h3", font=heading3_font, spacing1=4, spacing3=3)
        self.ai_text.tag_configure("md_list", lmargin1=16, lmargin2=32, spacing3=2)
        self.ai_text.tag_configure(
            "md_quote",
            lmargin1=20,
            lmargin2=30,
            foreground="#4a4a4a",
            spacing1=2,
            spacing3=4,
        )
        self.ai_text.tag_configure("md_bold", font=bold_font)
        self.ai_text.tag_configure("md_italic", font=italic_font)
        self.ai_text.tag_configure("md_code_inline", font=mono_font, background="#f3f3f3")
        self.ai_text.tag_configure(
            "md_code_block",
            font=mono_font,
            background="#f3f3f3",
            lmargin1=16,
            lmargin2=16,
            spacing1=4,
            spacing3=6,
        )
        self.ai_text.tag_configure(
            "md_table",
            font=mono_font,
            lmargin1=8,
            lmargin2=8,
            spacing1=2,
            spacing3=4,
        )
        self.ai_text.tag_configure("md_link", foreground="#0b57d0", underline=True)

    def _render_markdown_to_ai_text(self, text: str) -> None:
        lines = text.splitlines()
        in_code_block = False
        line_index = 0

        while line_index < len(lines):
            line = lines[line_index]
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                line_index += 1
                continue

            if in_code_block:
                self.ai_text.insert(tk.END, f"{line}\n", ("md_code_block",))
                line_index += 1
                continue

            if not line.strip():
                self.ai_text.insert(tk.END, "\n")
                line_index += 1
                continue

            if self._is_markdown_table_start(lines, line_index):
                line_index = self._render_markdown_table(lines, line_index)
                continue

            quote_match = re.match(r"^(\s*(?:>\s*)+)(.*)$", line)
            if quote_match:
                quote_prefix = quote_match.group(1)
                quote_content = quote_match.group(2)
                quote_level = max(1, quote_prefix.count(">"))
                self.ai_text.insert(tk.END, "▎" * quote_level + " ", ("md_quote",))
                self._insert_inline_markdown(quote_content, base_tags=("md_quote",))
                self.ai_text.insert(tk.END, "\n")
                line_index += 1
                continue

            heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2).strip()
                if level == 1:
                    tag = "md_h1"
                elif level == 2:
                    tag = "md_h2"
                else:
                    tag = "md_h3"
                self._insert_inline_markdown(content, base_tags=(tag,))
                self.ai_text.insert(tk.END, "\n")
                line_index += 1
                continue

            list_match = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
            if list_match:
                leading_spaces = list_match.group(1).replace("\t", "    ")
                marker = list_match.group(2)
                item = list_match.group(3).strip()
                indent_level = min(len(leading_spaces) // 2, 8)
                prefix = "  " * indent_level + (f"{marker} " if marker.endswith(".") else "• ")
                self.ai_text.insert(tk.END, prefix, ("md_list",))
                self._insert_inline_markdown(item, base_tags=("md_list",))
                self.ai_text.insert(tk.END, "\n")
                line_index += 1
                continue

            self._insert_inline_markdown(line.strip(), base_tags=("md_p",))
            self.ai_text.insert(tk.END, "\n")
            line_index += 1

    def _is_markdown_table_start(self, lines: list[str], start_index: int) -> bool:
        if start_index + 1 >= len(lines):
            return False

        header_line = lines[start_index]
        separator_line = lines[start_index + 1]
        if "|" not in header_line:
            return False

        return self._is_table_separator_line(separator_line)

    def _is_table_separator_line(self, line: str) -> bool:
        normalized = line.strip()
        if not normalized or "|" not in normalized:
            return False

        cells = self._split_table_row(normalized)
        if not cells:
            return False

        for cell in cells:
            if not re.fullmatch(r":?-{3,}:?", cell.strip()):
                return False
        return True

    def _split_table_row(self, line: str) -> list[str]:
        normalized = line.strip()
        if normalized.startswith("|"):
            normalized = normalized[1:]
        if normalized.endswith("|"):
            normalized = normalized[:-1]
        return [part.strip() for part in normalized.split("|")]

    def _render_markdown_table(self, lines: list[str], start_index: int) -> int:
        header_cells = self._split_table_row(lines[start_index])
        alignment_cells = self._split_table_row(lines[start_index + 1])

        rows: list[list[str]] = [header_cells]
        line_index = start_index + 2
        while line_index < len(lines):
            line = lines[line_index]
            if not line.strip() or "|" not in line:
                break
            rows.append(self._split_table_row(line))
            line_index += 1

        column_count = max(len(header_cells), len(alignment_cells), *(len(row) for row in rows))
        alignments: list[str] = []
        for index in range(column_count):
            marker = alignment_cells[index] if index < len(alignment_cells) else "---"
            stripped = marker.strip()
            if stripped.startswith(":") and stripped.endswith(":"):
                alignments.append("center")
            elif stripped.endswith(":"):
                alignments.append("right")
            else:
                alignments.append("left")

        normalized_rows: list[list[str]] = []
        for row in rows:
            normalized = row + [""] * (column_count - len(row))
            normalized_rows.append(normalized)

        widths = [0] * column_count
        for row in normalized_rows:
            for index, cell in enumerate(row):
                truncated = self._truncate_table_cell(cell)
                widths[index] = max(widths[index], len(truncated))

        widths = [min(width, self.MAX_TABLE_COLUMN_WIDTH) for width in widths]

        for row_index, row in enumerate(normalized_rows):
            rendered_row = self._format_table_row(row, widths, alignments)
            self.ai_text.insert(tk.END, f"{rendered_row}\n", ("md_table",))
            if row_index == 0:
                separator = "| " + " | ".join("-" * max(width, 3) for width in widths) + " |"
                self.ai_text.insert(tk.END, f"{separator}\n", ("md_table",))

        self.ai_text.insert(tk.END, "\n")
        return line_index

    def _format_table_row(self, row: list[str], widths: list[int], alignments: list[str]) -> str:
        rendered_cells: list[str] = []
        for index, cell in enumerate(row):
            width = widths[index]
            cell = self._truncate_table_cell(cell, width)
            align = alignments[index] if index < len(alignments) else "left"
            if align == "right":
                rendered_cells.append(cell.rjust(width))
            elif align == "center":
                rendered_cells.append(cell.center(width))
            else:
                rendered_cells.append(cell.ljust(width))

        return "| " + " | ".join(rendered_cells) + " |"

    def _truncate_table_cell(self, text: str, width_limit: int | None = None) -> str:
        limit = width_limit if width_limit is not None else self.MAX_TABLE_COLUMN_WIDTH
        if len(text) <= limit:
            return text
        if limit <= 3:
            return "." * limit
        return text[: limit - 3] + "..."

    def _insert_inline_markdown(self, text: str, base_tags: tuple[str, ...]) -> None:
        cursor = 0
        for match in self.INLINE_MARKDOWN_PATTERN.finditer(text):
            if match.start() > cursor:
                self.ai_text.insert(tk.END, text[cursor : match.start()], base_tags)

            token = match.group(0)
            tags = list(base_tags)

            if token.startswith("**") and token.endswith("**"):
                self._insert_inline_markdown(token[2:-2], base_tags=tuple(tags + ["md_bold"]))
                cursor = match.end()
                continue
            elif token.startswith("__") and token.endswith("__"):
                self._insert_inline_markdown(token[2:-2], base_tags=tuple(tags + ["md_bold"]))
                cursor = match.end()
                continue
            elif token.startswith("*") and token.endswith("*"):
                self._insert_inline_markdown(token[1:-1], base_tags=tuple(tags + ["md_italic"]))
                cursor = match.end()
                continue
            elif token.startswith("_") and token.endswith("_"):
                self._insert_inline_markdown(token[1:-1], base_tags=tuple(tags + ["md_italic"]))
                cursor = match.end()
                continue
            elif token.startswith("`") and token.endswith("`"):
                content = token[1:-1]
                tags.append("md_code_inline")
            elif token.startswith("[") and "](" in token and token.endswith(")"):
                label, url_part = token[1:-1].split("](", maxsplit=1)
                self._insert_clickable_link(label, url_part, tuple(tags + ["md_link"]))
                cursor = match.end()
                continue
            else:
                content = token

            self.ai_text.insert(tk.END, content, tuple(tags))
            cursor = match.end()

        if cursor < len(text):
            self.ai_text.insert(tk.END, text[cursor:], base_tags)

    def _insert_clickable_link(self, label: str, url: str, base_tags: tuple[str, ...]) -> None:
        start = self.ai_text.index(tk.END)
        self.ai_text.insert(tk.END, label, base_tags)
        end = self.ai_text.index(tk.END)

        link_tag = f"md_link_{self._link_tag_counter}"
        self._link_tag_counter += 1
        self.ai_text.tag_add(link_tag, start, end)
        self.ai_text.tag_configure(link_tag, foreground="#0b57d0", underline=True)
        self.ai_text.tag_bind(link_tag, "<Button-1>", lambda _event, target=url: self._open_link(target))
        self.ai_text.tag_bind(link_tag, "<Enter>", lambda _event, target=url: self._preview_link(target))
        self.ai_text.tag_bind(link_tag, "<Leave>", lambda _event: self._clear_link_preview())

    def _preview_link(self, url: str) -> None:
        if self._message_before_link_preview is None:
            self._message_before_link_preview = self.message_var.get()
        self.ai_text.configure(cursor="hand2")
        self.message_var.set(f"Link preview: {url}")

    def _clear_link_preview(self) -> None:
        self.ai_text.configure(cursor="xterm")
        if self._message_before_link_preview is None:
            return

        if self.message_var.get().startswith("Link preview: "):
            self.message_var.set(self._message_before_link_preview)
        self._message_before_link_preview = None

    def _open_link(self, url: str) -> None:
        try:
            webbrowser.open_new_tab(url)
        except Exception as exc:
            self.message_var.set(f"Failed to open link: {exc}")

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