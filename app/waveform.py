"""Wellenform-Darstellung für Audio."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
import numpy as np


class WaveformCanvas(ctk.CTkFrame):
    def __init__(self, master, height: int = 100, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._height = height
        self._audio: np.ndarray | None = None
        self._duration = 0.0
        self._position = 0.0
        self._on_seek = None

        self.canvas = tk.Canvas(
            self,
            height=height,
            highlightthickness=0,
            bg="#2b2b2b",
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)
        self.canvas.bind("<Configure>", lambda _e: self._redraw())
        self.canvas.bind("<Button-1>", self._on_click)

        self.time_label = ctk.CTkLabel(self, text="00:00 / 00:00", font=ctk.CTkFont(size=12))
        self.time_label.pack(pady=(0, 4))

    def set_seek_callback(self, callback) -> None:
        self._on_seek = callback

    def load_audio(self, audio: np.ndarray, sample_rate: int) -> None:
        self._audio = audio.astype(np.float32) if audio.size > 0 else None
        self._duration = len(audio) / sample_rate if audio.size > 0 else 0.0
        self._position = 0.0
        self._redraw()
        self._update_time_label()

    def set_position(self, position: float, duration: float | None = None) -> None:
        self._position = position
        if duration is not None:
            self._duration = duration
        self._redraw()
        self._update_time_label()

    def clear(self) -> None:
        self._audio = None
        self._duration = 0.0
        self._position = 0.0
        self._redraw()
        self._update_time_label()

    def _on_click(self, event) -> None:
        if self._duration <= 0 or not self._on_seek:
            return

        width = max(self.canvas.winfo_width(), 1)
        ratio = max(0.0, min(1.0, event.x / width))
        self._on_seek(ratio * self._duration)

    def _update_time_label(self) -> None:
        self.time_label.configure(
            text=f"{self._format_time(self._position)} / {self._format_time(self._duration)}"
        )

    @staticmethod
    def _format_time(seconds: float) -> str:
        total = int(seconds)
        minutes, secs = divmod(total, 60)
        return f"{minutes:02d}:{secs:02d}"

    def _redraw(self) -> None:
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        mid_y = height // 2

        self.canvas.create_rectangle(0, 0, width, height, fill="#2b2b2b", outline="")

        if self._audio is None or self._audio.size == 0:
            self.canvas.create_text(
                width // 2,
                mid_y,
                text="Keine Aufnahme",
                fill="#666666",
                font=("Segoe UI", 11),
            )
            return

        points = self._downsample(self._audio, width)
        amplitude = height * 0.42

        for x, value in enumerate(points):
            bar_height = max(1, int(abs(value) * amplitude))
            color = "#3b8ed0"
            self.canvas.create_line(
                x,
                mid_y - bar_height,
                x,
                mid_y + bar_height,
                fill=color,
            )

        if self._duration > 0:
            pos_x = int((self._position / self._duration) * width)
            self.canvas.create_line(pos_x, 0, pos_x, height, fill="#e74c3c", width=2)

    @staticmethod
    def _downsample(audio: np.ndarray, target_points: int) -> np.ndarray:
        if audio.size <= target_points:
            return audio

        chunk_size = audio.size // target_points
        trimmed = audio[: chunk_size * target_points]
        chunks = trimmed.reshape(target_points, chunk_size)
        return np.max(np.abs(chunks), axis=1)
