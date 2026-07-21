"""Hauptfenster der Audio-Transkriptions-App."""


from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable



import customtkinter as ctk
import numpy as np

from app.backends.base import BackendConfigurationError
from app.backends.factory import BackendFactory
from app.settings import AppSettings, load_settings, save_settings

from app.waveform import WaveformCanvas

from app.widgets import labeled_checkbox, labeled_option_menu
from core.audio_player import AudioPlayer
from core.audio_processor import AudioProcessor, EnhancementOptions
from core.audio_recorder import AudioRecorder, RecordingConfig, SAMPLE_RATE
from core.docx_exporter import default_title, export_to_docx
from core.storage import SessionStorage


_ALLOWED_BACKEND_KEYS = ["faster_whisper", "whispercpp", "azure_openai"]


class AudioTranscriptionApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("Audio-Transkription")
        self.geometry("920x920")
        self.minsize(860, 820)

        self.recorder = AudioRecorder(sample_rate=SAMPLE_RATE)
        self.player = AudioPlayer(sample_rate=SAMPLE_RATE)

        self.processor = AudioProcessor(sample_rate=SAMPLE_RATE)
        self._settings: AppSettings = load_settings()
        self.backend_factory = BackendFactory()
        self.transcriber = self._create_backend_from_settings()
        self.storage = SessionStorage()
        self._init_warnings: list[str] = []

        self.raw_audio = np.array([], dtype=np.float32)

        self.enhanced_audio: np.ndarray | None = None
        self.transcript_text = ""
        self.enhancement_steps: list[str] = []

        self._worker: threading.Thread | None = None
        self._input_devices: list = []
        self._loopback_devices: list = []
        self._source_audio_path: Path | None = None


        self.player.set_callbacks(
            on_position_change=self._on_player_position,
            on_finished=self._on_player_finished,
        )

        self._build_ui()
        self._refresh_devices()


        self._show_init_warnings()
        self._set_status("Bereit")


    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Audio-Transkription",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        settings_frame = ctk.CTkFrame(self)

        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        settings_frame.grid_columnconfigure(1, weight=1)

        settings_frame.grid_columnconfigure(3, weight=1)
        settings_frame.grid_columnconfigure(4, weight=0)
        settings_frame.grid_columnconfigure(5, weight=0)



        mic_label, self.device_menu = labeled_option_menu(
            settings_frame,
            "Mikrofon:",
            values=["Kein Gerät"],
            default="Kein Gerät",
            width=320,
        )
        mic_label.grid(row=0, column=0, padx=12, pady=10, sticky="w")
        self.device_menu.grid(row=0, column=1, padx=12, pady=10, sticky="ew")

        model_values = list(self.transcriber.MODEL_SIZES) or ["small"]
        preferred_model = self._settings.backend_options.get("model_size", "small")

        if preferred_model not in model_values:
            preferred_model = model_values[0]
        model_label, self.model_menu = labeled_option_menu(
            settings_frame,
            "Whisper-Modell:",
            values=model_values,
            default=preferred_model,
            width=160,
        )

        model_label.grid(row=0, column=2, padx=12, pady=10, sticky="w")
        self.model_menu.grid(row=0, column=3, padx=12, pady=10, sticky="ew")

        backend_values = self.backend_factory.available_backends()
        filtered_backend_values = [
            backend_key for backend_key in backend_values if backend_key in _ALLOWED_BACKEND_KEYS
        ]
        if not filtered_backend_values:
            filtered_backend_values = backend_values
        backend_default = self._settings.backend if self._settings.backend in filtered_backend_values else filtered_backend_values[0]
        backend_label, self.backend_menu = labeled_option_menu(
            settings_frame,
            "Transkriptions-Backend:",
            values=filtered_backend_values,
            default=backend_default,
            width=220,
        )

        backend_label.grid(row=0, column=4, padx=12, pady=10, sticky="w")
        self.backend_menu.grid(row=0, column=5, padx=12, pady=10, sticky="ew")
        self.backend_menu.configure(command=self._on_backend_selected)

        lang_label, self.language_menu = labeled_option_menu(


            settings_frame,
            "Sprache:",
            values=["de", "en", "auto"],
            default="de",
            width=160,
        )
        lang_label.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="w")
        self.language_menu.grid(row=1, column=1, padx=12, pady=(0, 8), sticky="w")

        execution_values = self.transcriber.available_execution_modes()
        execution_default = self._settings.backend_options.get("execution_mode", "auto")

        if execution_default not in execution_values:
            execution_default = execution_values[0]
        execution_label, self.execution_menu = labeled_option_menu(
            settings_frame,
            "Rechenmodus:",
            values=execution_values,
            default=execution_default,
            width=160,
        )


        execution_label.grid(row=1, column=2, padx=12, pady=(0, 8), sticky="w")

        self.execution_menu.grid(row=1, column=3, padx=12, pady=(0, 8), sticky="w")

        self.cuda_diagnostic_button = ctk.CTkButton(
            settings_frame,
            text="CUDA prüfen",
            command=self._show_cuda_diagnostics,
            width=130,
        )
        self.cuda_diagnostic_button.grid(row=1, column=4, padx=12, pady=(0, 8), sticky="e")

        self.chk_speaker_diarization = labeled_checkbox(

            settings_frame,
            "Sprecher unterscheiden",
            default=False,
        )
        self.chk_speaker_diarization.configure(command=self._toggle_speaker_diarization)
        self.chk_speaker_diarization.grid(row=2, column=2, padx=12, pady=4, sticky="w")

        speaker_count_label, self.speaker_count_menu = labeled_option_menu(
            settings_frame,
            "Max. Sprecher:",
            values=["2", "3", "4", "5", "6"],
            default="2",
            width=160,
        )
        self._speaker_count_label = speaker_count_label
        speaker_count_label.grid(row=3, column=2, padx=12, pady=(0, 12), sticky="w")
        self.speaker_count_menu.grid(row=3, column=3, padx=12, pady=(0, 12), sticky="w")
        self._set_speaker_controls_enabled(False)





        self.chk_system_audio = labeled_checkbox(

            settings_frame,
            "System-Audio mitschneiden (Teams, Browser, …)",
            default=False,
        )
        self.chk_system_audio.grid(row=2, column=0, columnspan=2, padx=12, pady=4, sticky="w")
        self.chk_system_audio.configure(command=self._toggle_system_audio)


        loopback_label, self.loopback_menu = labeled_option_menu(
            settings_frame,
            "System-Ausgabe:",
            values=["Nicht verfügbar"],
            default="Nicht verfügbar",
            width=320,
        )
        loopback_label.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="w")
        self.loopback_menu.grid(row=3, column=1, padx=12, pady=(0, 12), sticky="ew")
        self._loopback_label = loopback_label
        self._set_loopback_enabled(False)

        enhance_frame = ctk.CTkFrame(self)
        enhance_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        enhance_frame.grid_columnconfigure(4, weight=1)

        enhance_title = ctk.CTkLabel(
            enhance_frame,
            text="Audio verbessern (vor Transkription)",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        enhance_title.grid(row=0, column=0, columnspan=5, padx=12, pady=(12, 6), sticky="w")

        self.chk_normalize = labeled_checkbox(enhance_frame, "Normalisieren")
        self.chk_high_pass = labeled_checkbox(enhance_frame, "Hochpassfilter")
        self.chk_noise_reduce = labeled_checkbox(enhance_frame, "Rauschreduktion")
        self.chk_auto_enhance = labeled_checkbox(
            enhance_frame,
            "Automatisch vor Transkription",
            default=True,
        )

        self.chk_normalize.grid(row=1, column=0, padx=12, pady=8, sticky="w")
        self.chk_high_pass.grid(row=1, column=1, padx=12, pady=8, sticky="w")
        self.chk_noise_reduce.grid(row=1, column=2, padx=12, pady=8, sticky="w")
        self.chk_auto_enhance.grid(row=1, column=3, padx=12, pady=8, sticky="w")

        self.enhance_button = ctk.CTkButton(
            enhance_frame,
            text="Jetzt verbessern",
            command=self._enhance_audio,
            width=150,
        )
        self.enhance_button.grid(row=1, column=4, padx=12, pady=8, sticky="e")

        self.enhance_info = ctk.CTkLabel(
            enhance_frame,
            text="Noch keine Verbesserung angewendet.",
            text_color="gray",
        )
        self.enhance_info.grid(row=2, column=0, columnspan=5, padx=12, pady=(0, 12), sticky="w")

        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.record_button = ctk.CTkButton(

            action_frame,
            text="Aufnahme starten",
            command=self._toggle_recording,
            fg_color="#c0392b",
            hover_color="#922b21",
            width=170,
        )
        self.record_button.pack(side="left", padx=12, pady=12)

        self.pause_record_button = ctk.CTkButton(
            action_frame,
            text="Pause",
            command=self._toggle_recording_pause,
            width=110,
            state="disabled",
        )
        self.pause_record_button.pack(side="left", padx=12, pady=12)

        self.load_button = ctk.CTkButton(
            action_frame,
            text="Aufnahme laden",
            command=self._load_audio_file,
            width=150,
        )
        self.load_button.pack(side="left", padx=12, pady=12)

        self.transcribe_button = ctk.CTkButton(
            action_frame,
            text="Transkribieren",
            command=self._start_transcription,
            width=150,
        )

        self.transcribe_button.pack(side="left", padx=12, pady=12)

        self.status_label = ctk.CTkLabel(action_frame, text="Status: Bereit")
        self.status_label.pack(side="left", padx=20)

        player_frame = ctk.CTkFrame(self)
        player_frame.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        player_frame.grid_columnconfigure(0, weight=1)

        player_title = ctk.CTkLabel(
            player_frame,
            text="Wiedergabe",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        player_title.grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")

        self.waveform = WaveformCanvas(player_frame, height=110)
        self.waveform.grid(row=1, column=0, padx=8, pady=4, sticky="ew")
        self.waveform.set_seek_callback(self._seek_from_waveform)

        controls = ctk.CTkFrame(player_frame, fg_color="transparent")
        controls.grid(row=2, column=0, padx=12, pady=(4, 12), sticky="ew")

        self.rewind_button = ctk.CTkButton(
            controls, text="-10 s", command=lambda: self._skip(-10), width=70
        )
        self.rewind_button.pack(side="left", padx=4)

        self.play_pause_button = ctk.CTkButton(
            controls, text="Abspielen", command=self._toggle_playback, width=110
        )
        self.play_pause_button.pack(side="left", padx=4)

        self.forward_button = ctk.CTkButton(
            controls, text="+10 s", command=lambda: self._skip(10), width=70
        )
        self.forward_button.pack(side="left", padx=4)

        self.stop_button = ctk.CTkButton(
            controls, text="Stopp", command=self._stop_playback, width=70
        )
        self.stop_button.pack(side="left", padx=4)

        self.source_menu_label = ctk.CTkLabel(controls, text="Quelle:")
        self.source_menu_label.pack(side="left", padx=(16, 4))

        self.preview_source_menu = ctk.CTkOptionMenu(
            controls,
            values=["Aufnahme", "Verbessert"],
            command=self._on_preview_source_change,
            width=130,
        )
        self.preview_source_menu.set("Aufnahme")
        self.preview_source_menu.pack(side="left", padx=4)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=5, column=0, padx=20, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="nsew")

        save_frame = ctk.CTkFrame(self)
        save_frame.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")

        ctk.CTkButton(
            save_frame,
            text="Roh-Aufnahme speichern",
            command=self._save_raw_recording,
            width=170,
        ).pack(side="left", padx=12, pady=12)

        ctk.CTkButton(
            save_frame,
            text="Verbesserte Aufnahme speichern",
            command=self._save_enhanced_recording,
            width=200,
        ).pack(side="left", padx=12, pady=12)

        ctk.CTkButton(
            save_frame,
            text="Als DOCX exportieren",
            command=self._export_docx,
            width=160,
        ).pack(side="left", padx=12, pady=12)

        ctk.CTkButton(

            save_frame,
            text="Alles speichern",
            command=self._save_all,
            width=150,
        ).pack(side="left", padx=12, pady=12)

        self._refresh_backend_dependent_controls()

    
    def _set_loopback_enabled(self, enabled: bool) -> None:


        state = "normal" if enabled else "disabled"
        self.loopback_menu.configure(state=state)
        self._loopback_label.configure(
            text_color=("gray10", "gray90") if enabled else "gray"
        )


    def _show_init_warnings(self) -> None:
        while self._init_warnings:
            messagebox.showwarning(
                "Backend-Konfiguration",
                self._init_warnings.pop(0),
            )

    def _speaker_diarization_enabled(self) -> bool:

        return bool(self.chk_speaker_diarization.get())

    def _speaker_count(self) -> int:
        return int(self.speaker_count_menu.get())

    def _speaker_settings(self) -> tuple[bool, int]:
        if not self._speaker_diarization_enabled():
            return False, 1
        return True, self._speaker_count()

    def _speaker_metadata(self) -> str | None:
        if not self._speaker_diarization_enabled():
            return None
        return f"Aktiv (max. {self._speaker_count()} Sprecher)"

    def _set_speaker_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.speaker_count_menu.configure(state=state)
        self._speaker_count_label.configure(text_color=("gray10", "gray90") if enabled else "gray")

    def _toggle_speaker_diarization(self) -> None:
        self._set_speaker_controls_enabled(self._speaker_diarization_enabled())

    def _toggle_system_audio(self) -> None:
        enabled = bool(self.chk_system_audio.get())

        self._set_loopback_enabled(enabled)
        if enabled and not self._loopback_devices:
            messagebox.showwarning(
                "Hinweis",
                "System-Audio-Aufnahme ist nur unter Windows mit WASAPI verfügbar.",
            )
            self.chk_system_audio.deselect()
            self._set_loopback_enabled(False)

    def _refresh_devices(self) -> None:
        devices = self.recorder.list_input_devices()
        if not devices:
            self.device_menu.configure(values=["Kein Gerät"])
            self.device_menu.set("Kein Gerät")
            self._input_devices = []
        else:
            names = [device.name for device in devices]
            self._input_devices = devices
            self.device_menu.configure(values=names)
            self.device_menu.set(names[0])

        self._loopback_devices = self.recorder.list_loopback_devices()
        if self._loopback_devices:
            loopback_names = [device.name for device in self._loopback_devices]
            self.loopback_menu.configure(values=loopback_names)
            self.loopback_menu.set(loopback_names[0])
            if AudioRecorder.loopback_supported():
                self.chk_system_audio.configure(state="normal")
        else:
            self.loopback_menu.configure(values=["Nicht verfügbar"])
            self.loopback_menu.set("Nicht verfügbar")
            self.chk_system_audio.configure(state="disabled")

    def _selected_device_index(self) -> int | None:
        selected_name = self.device_menu.get()
        for device in self._input_devices:
            if device.name == selected_name:
                return device.index
        return None

    def _selected_loopback_index(self) -> int | None:
        if not bool(self.chk_system_audio.get()):
            return None
        selected_name = self.loopback_menu.get()
        for device in self._loopback_devices:
            if device.name == selected_name:
                return device.index
        return None

    def _preview_audio(self) -> np.ndarray:
        if self.preview_source_menu.get() == "Verbessert" and self.enhanced_audio is not None:
            return self.enhanced_audio
        return self.raw_audio

    def _reload_player(self) -> None:
        audio = self._preview_audio()
        self.player.load(audio)
        self.waveform.load_audio(audio, SAMPLE_RATE)

    def _on_preview_source_change(self, _value: str) -> None:
        was_playing = self.player.is_playing
        position_ratio = (
            self.player.position / self.player.duration if self.player.duration > 0 else 0
        )
        self._reload_player()
        if was_playing and self.player.duration > 0:
            self.player.seek(position_ratio * self.player.duration)
            self.player.play()
        elif self.player.duration > 0:
            self.player.seek(position_ratio * self.player.duration)

    def _enhancement_options(self) -> EnhancementOptions:
        return EnhancementOptions(
            normalize=bool(self.chk_normalize.get()),
            high_pass=bool(self.chk_high_pass.get()),
            noise_reduce=bool(self.chk_noise_reduce.get()),
        )

    def _set_status(self, message: str) -> None:
        self.status_label.configure(text=f"Status: {message}")

    def _backend_config(self) -> dict[str, Any]:
        backend_key = self._normalize_backend_selection()
        return {
            "backend": backend_key,
                        "options": self._settings.backend_options,
        }








    def _normalize_backend_selection(self) -> str:
        backend_key = self._settings.backend
        if backend_key not in _ALLOWED_BACKEND_KEYS:
            backend_key = _ALLOWED_BACKEND_KEYS[0]
            self._settings.backend = backend_key
            self._settings.backend_options = {}
            save_settings(self._settings)
        return backend_key

    def _create_backend_from_settings(self):
        config = self._backend_config()
        try:
            backend = self.backend_factory.create_backend(config)
            backend.initialize()
            return backend
        except BackendConfigurationError as exc:
            self._init_warnings.append(
                f"{exc}\nBackend zurückgesetzt auf '{_ALLOWED_BACKEND_KEYS[0]}' und wird neu geladen."
            )
            self._settings.backend = _ALLOWED_BACKEND_KEYS[0]
            self._settings.backend_options = {}
            save_settings(self._settings)
            config = self._backend_config()
            backend = self.backend_factory.create_backend(config)
            backend.initialize()
            return backend



    def _on_backend_selected(self, backend_key: str) -> None:
        if backend_key == self._settings.backend:
            return
        self.transcriber.cleanup()
        self._settings.backend = backend_key
        self._settings.backend_options = {}
        save_settings(self._settings)
        self.transcriber = self._create_backend_from_settings()
        self._refresh_backend_dependent_controls()
        self._set_status(f"Backend gewechselt zu {backend_key}")

    def _refresh_backend_dependent_controls(self) -> None:
        model_values = list(self.transcriber.MODEL_SIZES) or ["small"]
        self.model_menu.configure(values=model_values)
        if self.model_menu.get() not in model_values:
            self.model_menu.set(model_values[0])
        execution_values = self.transcriber.available_execution_modes()
        if execution_values:
            self.execution_menu.configure(values=execution_values)
            if self.execution_menu.get() not in execution_values:
                self.execution_menu.set(execution_values[0])
        backend_supports_gpu = type(self.transcriber).supports_gpu()
        state = "normal" if backend_supports_gpu else "disabled"
        self.cuda_diagnostic_button.configure(state=state)

    def _show_cuda_diagnostics(self) -> None:

        diag_provider = getattr(type(self.transcriber), "cuda_diagnostic_report", None)
        if diag_provider and type(self.transcriber).supports_gpu():
            report = diag_provider()
        else:
            report = "CUDA-Diagnose ist für dieses Backend nicht verfügbar."

        dialog = ctk.CTkToplevel(self)

        dialog.title("CUDA-Diagnose")
        dialog.geometry("760x560")
        dialog.minsize(680, 480)
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Escape>", lambda _event: dialog.destroy())

        title = ctk.CTkLabel(
            dialog,
            text="CUDA-Diagnose",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        textbox = ctk.CTkTextbox(dialog, wrap="word")
        textbox.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        textbox.insert("1.0", report)
        textbox.configure(state="disabled")

        button_row = ctk.CTkFrame(dialog, fg_color="transparent")
        button_row.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="e")

        def copy_report() -> None:
            self.clipboard_clear()
            self.clipboard_append(report)
            self._set_status("CUDA-Diagnose in die Zwischenablage kopiert")

        ctk.CTkButton(
            button_row,
            text="In Zwischenablage kopieren",
            command=copy_report,
            width=190,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_row,
            text="Schließen",
            command=dialog.destroy,
            width=120,
        ).pack(side="left")

    def _set_widgets_state(self, widgets: list, state: str) -> None:

        for widget in widgets:
            widget.configure(state=state)

    def _sync_recording_controls(self) -> None:
        if self.recorder.is_recording:
            self.record_button.configure(text="Aufnahme stoppen", fg_color="#27ae60")
            self.pause_record_button.configure(
                text="Fortsetzen" if self.recorder.is_paused else "Pause",
                state="normal",
            )
            self.load_button.configure(state="disabled")
        else:
            self.record_button.configure(text="Aufnahme starten", fg_color="#c0392b")
            self.pause_record_button.configure(text="Pause", state="disabled")
            self.load_button.configure(state="normal")

        
    def _clear_audio_workflow_state(self, *, reset_preview_source: bool = True) -> None:



        self.enhanced_audio = None
        self.transcript_text = ""
        self.enhancement_steps = []
        self._source_audio_path = None
        self.enhance_info.configure(text="Noch keine Verbesserung angewendet.")
        self.textbox.delete("1.0", "end")
        self.progress.set(0)
        if reset_preview_source:
            self.preview_source_menu.set("Aufnahme")

    def _start_worker(self, work: Callable[[], None]) -> None:
        self._worker = threading.Thread(target=work, daemon=True)
        self._worker.start()

    def _recording_mode_text(self, include_system: bool) -> str:
        return "Mikrofon + System" if include_system else "Mikrofon"

    def _transcription_settings(self) -> tuple[bool, int]:
        return self._speaker_settings()


    
    def _finalize_recording(self) -> None:


        self.raw_audio = self.recorder.stop()
        self._clear_audio_workflow_state()
        self._sync_recording_controls()
        duration = len(self.raw_audio) / SAMPLE_RATE if self.raw_audio.size else 0
        self._set_status(f"Aufnahme beendet ({duration:.1f} s)")
        self._reload_player()

    def _prepare_recording_session(self, include_system: bool) -> None:
        self.raw_audio = np.array([], dtype=np.float32)
        self._clear_audio_workflow_state()
        self.waveform.clear()
        self._sync_recording_controls()
        self._set_status(f"Aufnahme läuft ({self._recording_mode_text(include_system)})...")

    def _apply_loaded_audio(self, audio: np.ndarray, source_path: Path) -> None:
        self.player.stop()
        self.raw_audio = audio
        self._clear_audio_workflow_state()
        self._source_audio_path = source_path
        self._sync_recording_controls()
        self._reload_player()



    
    def _set_busy(self, busy: bool) -> None:

        state = "disabled" if busy else "normal"
        self._set_widgets_state(
            [
                self.record_button,
                self.transcribe_button,
                self.enhance_button,
                self.play_pause_button,
                self.rewind_button,
                self.forward_button,
                self.stop_button,
                self.load_button,
                self.chk_speaker_diarization,
                self.chk_system_audio,
                self.chk_normalize,
                self.chk_high_pass,
                self.chk_noise_reduce,
                self.chk_auto_enhance,
            ],
            state,
        )

        if busy:
            self.pause_record_button.configure(state="disabled")
            self._set_speaker_controls_enabled(False)
            return

        self._sync_recording_controls()
        self._set_speaker_controls_enabled(
            self._speaker_diarization_enabled() and not self.recorder.is_recording
        )







    def _toggle_recording(self) -> None:


        if self.recorder.is_recording:
            self._finalize_recording()
            return

        device_index = self._selected_device_index()
        if device_index is None:
            messagebox.showerror("Fehler", "Kein Mikrofon ausgewählt.")
            return

        include_system = bool(self.chk_system_audio.get())
        loopback_index = self._selected_loopback_index()
        if include_system and loopback_index is None:
            messagebox.showerror("Fehler", "Bitte eine System-Ausgabe für Loopback wählen.")
            return

        config = RecordingConfig(
            mic_device_index=device_index,
            include_system_audio=include_system,
            loopback_device_index=loopback_index,
        )

        try:
            self.player.stop()
            self.recorder.start(config)
        except Exception as exc:
            messagebox.showerror("Aufnahmefehler", str(exc))
            return

        self._prepare_recording_session(include_system)



    def _toggle_recording_pause(self) -> None:




        if not self.recorder.is_recording:
            return

        if self.recorder.is_paused:
            self.recorder.resume()
            self._sync_recording_controls()
            self._set_status(
                f"Aufnahme läuft ({self._recording_mode_text(bool(self.chk_system_audio.get()))})..."
            )
            return

        self.recorder.pause()
        self._sync_recording_controls()
        self._set_status("Aufnahme pausiert")



    def _load_audio_file(self) -> None:




        if self.recorder.is_recording:
            messagebox.showwarning("Hinweis", "Bitte die laufende Aufnahme zuerst stoppen.")
            return

        path = filedialog.askopenfilename(
            title="Audiodatei auswählen",
            filetypes=[
                ("Audiodateien", "*.wav *.flac *.ogg *.mp3 *.m4a *.aac *.wma"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not path:
            return

        try:
            audio = AudioRecorder.load_audio_file(path, target_sample_rate=SAMPLE_RATE)
        except Exception as exc:
            messagebox.showerror("Ladefehler", f"Datei konnte nicht geladen werden:\n{exc}")
            return

        if audio.size == 0:
            messagebox.showwarning(
                "Hinweis",
                "Die gewählte Audiodatei enthält keine verwertbaren Audiodaten.",
            )
            return

        self._apply_loaded_audio(audio, Path(path))
        duration = len(self.raw_audio) / SAMPLE_RATE if self.raw_audio.size else 0
        self._set_status(f"Datei geladen: {Path(path).name} ({duration:.1f} s)")


    def _enhance_audio(self) -> None:




        if self.recorder.is_recording:
            messagebox.showwarning("Hinweis", "Bitte die laufende Aufnahme zuerst stoppen.")
            return

        if self.raw_audio.size == 0:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine Aufnahme erstellen oder laden.")
            return

        options = self._enhancement_options()
        if not any((options.normalize, options.high_pass, options.noise_reduce)):
            messagebox.showwarning(
                "Hinweis",
                "Bitte mindestens eine Verbesserungsoption aktivieren.",
            )
            return

        self._set_busy(True)
        self._set_status("Audio wird verbessert...")
        self.progress.set(0.3)

        def work() -> None:
            try:
                result = self.processor.enhance(self.raw_audio, options)
            except Exception as exc:
                error_message = str(exc)
                self.after(0, lambda message=error_message: self._on_enhance_error(message))
                return

            self.after(0, lambda: self._on_enhance_done(result.audio, result.applied_steps))

        self._start_worker(work)


    def _on_enhance_done(self, audio: np.ndarray, steps: list[str]) -> None:
        self.enhanced_audio = audio
        self.enhancement_steps = steps
        self.progress.set(1.0)
        self._set_busy(False)
        self._set_status("Audio verbessert")
        self.enhance_info.configure(
            text="Angewendet: " + (", ".join(steps) if steps else "Keine Schritte"),
            text_color=("gray10", "gray90"),
        )
        self.preview_source_menu.set("Verbessert")
        self._reload_player()

    def _on_enhance_error(self, message: str) -> None:
        self.progress.set(0)
        self._set_busy(False)
        self._set_status("Fehler bei Audio-Verbesserung")
        messagebox.showerror("Fehler", message)

    def _audio_for_transcription(self) -> np.ndarray:
        if self.enhanced_audio is not None:
            return self.enhanced_audio

        if bool(self.chk_auto_enhance.get()):
            options = self._enhancement_options()
            if any((options.normalize, options.high_pass, options.noise_reduce)):
                try:
                    result = self.processor.enhance(self.raw_audio, options)
                except Exception as exc:
                    raise RuntimeError(
                        f"Automatische Audio-Verbesserung fehlgeschlagen: {exc}"
                    ) from exc
                self.enhanced_audio = result.audio
                self.enhancement_steps = result.applied_steps
                self.enhance_info.configure(
                    text="Automatisch angewendet: " + ", ".join(result.applied_steps),
                    text_color=("gray10", "gray90"),
                )
                return result.audio

        return self.raw_audio

    def _start_transcription(self) -> None:




        if self.recorder.is_recording:
            messagebox.showwarning("Hinweis", "Bitte die laufende Aufnahme zuerst stoppen.")
            return

        if self.raw_audio.size == 0:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine Aufnahme erstellen oder laden.")
            return

        if self._worker and self._worker.is_alive():
            return

        speaker_diarization, max_speakers = self._transcription_settings()

        self._set_busy(True)
        self.progress.set(0.1)
        self._set_status("Vorbereitung...")

        def work() -> None:
            try:
                audio = self._audio_for_transcription()
                result = self.transcriber.transcribe(
                    audio=audio,
                    sample_rate=SAMPLE_RATE,
                    model_size=self.model_menu.get(),
                    language=self.language_menu.get(),
                    execution_mode=self.execution_menu.get(),
                    speaker_diarization=speaker_diarization,
                    max_speakers=max_speakers,
                    on_progress=lambda msg: self.after(0, lambda: self._set_status(msg)),
                )
            except Exception as exc:
                error_message = str(exc)
                self.after(0, lambda message=error_message: self._on_transcribe_error(message))
                return

            self.after(0, lambda: self._on_transcribe_done(result.text))

        self._start_worker(work)


    def _on_transcribe_done(self, text: str) -> None:
        self._worker = None
        self.transcript_text = text

        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)
        self.progress.set(1.0)
        self._set_busy(False)
        self._set_status("Transkription abgeschlossen")

    def _on_transcribe_error(self, message: str) -> None:
        self._worker = None
        self.progress.set(0)
        self._set_busy(False)
        self._set_status("Transkriptionsfehler")
        messagebox.showerror("Fehler", message)

    def _toggle_playback(self) -> None:
        audio = self._preview_audio()
        if audio.size == 0:
            messagebox.showwarning("Hinweis", "Keine Aufnahme zum Abspielen vorhanden.")
            return

        if self.player.is_playing:
            self.player.pause()
            self.play_pause_button.configure(text="Abspielen")
            self._set_status("Wiedergabe pausiert")
            return

        if self.player.is_paused:
            self.player.play()
            self.play_pause_button.configure(text="Pause")
            self._set_status("Wiedergabe läuft")
            return

        self.player.load(audio)
        self.player.play()
        self.play_pause_button.configure(text="Pause")
        self._set_status("Wiedergabe läuft")

    def _stop_playback(self) -> None:
        self.player.stop()
        self.play_pause_button.configure(text="Abspielen")
        self._set_status("Wiedergabe gestoppt")

    def _skip(self, seconds: float) -> None:
        if not self.player.has_audio:
            self._reload_player()
        if not self.player.has_audio:
            return
        self.player.skip(seconds)

    def _seek_from_waveform(self, seconds: float) -> None:
        if not self.player.has_audio:
            self._reload_player()
        if not self.player.has_audio:
            return
        self.player.seek(seconds)

    def _on_player_position(self, position: float, duration: float) -> None:
        self.after(0, lambda: self.waveform.set_position(position, duration))

        
    def _on_player_finished(self) -> None:
        self.after(0, lambda: self.play_pause_button.configure(text="Abspielen"))
        self.after(0, lambda: self._set_status("Wiedergabe beendet"))


    def _save_raw_recording(self) -> None:
        if self.raw_audio.size == 0:
            messagebox.showwarning("Hinweis", "Keine Roh-Aufnahme vorhanden.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV-Dateien", "*.wav")],
            initialfile=f"aufnahme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
        )
        if not path:
            return

        self.storage.save_wav(Path(path), self.raw_audio, SAMPLE_RATE)
        messagebox.showinfo("Gespeichert", f"Roh-Aufnahme gespeichert:\n{path}")

    def _save_enhanced_recording(self) -> None:
        if self.enhanced_audio is None or self.enhanced_audio.size == 0:
            messagebox.showwarning(
                "Hinweis",
                "Keine verbesserte Aufnahme vorhanden. Bitte zuerst verbessern.",
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV-Dateien", "*.wav")],
            initialfile=f"aufnahme_verbessert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
        )
        if not path:
            return

        self.storage.save_wav(Path(path), self.enhanced_audio, SAMPLE_RATE)
        messagebox.showinfo("Gespeichert", f"Verbesserte Aufnahme gespeichert:\n{path}")

    def _export_docx(self) -> None:
        if not self.transcript_text.strip():
            messagebox.showwarning("Hinweis", "Kein Transkript zum Exportieren vorhanden.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word-Dokumente", "*.docx")],
            initialfile=f"transkript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
        )
        if not path:
            return

        export_to_docx(
            text=self.transcript_text,
            output_path=Path(path),
            title=default_title(),
            metadata=self._build_metadata(),
        )
        messagebox.showinfo("Exportiert", f"DOCX gespeichert:\n{path}")

    def _save_all(self) -> None:
        if self.raw_audio.size == 0:
            messagebox.showwarning("Hinweis", "Keine Aufnahme vorhanden.")
            return
        if not self.transcript_text.strip():
            messagebox.showwarning("Hinweis", "Kein Transkript vorhanden.")
            return

        session = self.storage.save_all(
            raw_audio=self.raw_audio,
            enhanced_audio=self.enhanced_audio,
            transcript=self.transcript_text,
            sample_rate=SAMPLE_RATE,
            metadata=self._build_metadata(),
        )
        messagebox.showinfo("Gespeichert", f"Alles gespeichert in:\n{session.folder}")

    def _build_metadata(self) -> dict[str, str]:
        metadata = {

            "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "Mikrofon": self.device_menu.get(),
            "Whisper-Modell": self.model_menu.get(),
            "Sprache": self.language_menu.get(),
            "Rechenmodus": self.execution_menu.get(),
            "Dauer (s)": f"{len(self.raw_audio) / SAMPLE_RATE:.1f}",
        }
        metadata["Backend"] = self._settings.backend

        if self._source_audio_path is not None:

            metadata["Quelldatei"] = str(self._source_audio_path)
        if bool(self.chk_system_audio.get()):
            metadata["System-Audio"] = self.loopback_menu.get()
        speaker_metadata = self._speaker_metadata()
        if speaker_metadata is not None:
            metadata["Sprecher-Unterscheidung"] = speaker_metadata

        if self.enhancement_steps:
            metadata["Audio-Verbesserung"] = ", ".join(self.enhancement_steps)
        return metadata










