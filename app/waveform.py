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
        self._base_envelope: np.ndarray | None = None
        self._duration = 0.0
        self._position = 0.0
        self._on_seek = None
        self._cached_width = 0
        self._cached_height = 0
        self._playhead_id: int | None = None

        self.canvas = tk.Canvas(
            self,
            height=height,
            highlightthickness=0,
            bg="#2b2b2b",
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._on_click)

        self.time_label = ctk.CTkLabel(self, text="00:00 / 00:00", font=ctk.CTkFont(size=12))
        self.time_label.pack(pady=(0, 4))

    def set_seek_callback(self, callback) -> None:
        self._on_seek = callback

    def load_audio(self, audio: np.ndarray, sample_rate: int) -> None:
        if audio.size > 0:
            self._audio = audio.astype(np.float32, copy=False)
            self._base_envelope = self._compute_base_envelope(self._audio)
            self._duration = len(audio) / sample_rate
        else:
            self._audio = None
            self._base_envelope = None
            self._duration = 0.0
        self._position = 0.0
        self._redraw_static()
        self._update_time_label()

    def set_position(self, position: float, duration: float | None = None) -> None:
        self._position = position
        if duration is not None:
            self._duration = duration
        self._update_playhead()
        self._update_time_label()

    def clear(self) -> None:
        self._audio = None
        self._base_envelope = None
        self._duration = 0.0
        self._position = 0.0
        self._redraw_static()
        self._update_time_label()

    def _on_click(self, event) -> None:
        if self._duration <= 0 or not self._on_seek:
            return

        width = max(self.canvas.winfo_width(), 1)
        ratio = max(0.0, min(1.0, event.x / width))
        self._on_seek(ratio * self._duration)

    def _on_configure(self, _event) -> None:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        if width == self._cached_width and height == self._cached_height:
            return
        self._redraw_static()

    def _update_time_label(self) -> None:
        self.time_label.configure(
            text=f"{self._format_time(self._position)} / {self._format_time(self._duration)}"
        )

    @staticmethod
    def _format_time(seconds: float) -> str:
        total = int(seconds)
        minutes, secs = divmod(total, 60)
        return f"{minutes:02d}:{secs:02d}"

    def _redraw_static(self) -> None:
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self._cached_width = width
        self._cached_height = height
        mid_y = height // 2

        self.canvas.create_rectangle(0, 0, width, height, fill="#2b2b2b", outline="")

        if self._audio is None or self._audio.size == 0 or self._base_envelope is None:
            self.canvas.create_text(
                width // 2,
                mid_y,
                text="Keine Aufnahme",
                fill="#666666",
                font=("Segoe UI", 11),
            )
            self._playhead_id = None
            return

        points = self._resample_envelope(self._base_envelope, width)
        amplitude = height * 0.42
        upper_y = mid_y - (points * amplitude)
        lower_y = mid_y + (points * amplitude)

        polygon_coords: list[float] = []
        for x in range(width):
            polygon_coords.extend((x, float(upper_y[x])))
        for x in range(width - 1, -1, -1):
            polygon_coords.extend((x, float(lower_y[x])))

        self.canvas.create_polygon(polygon_coords, fill="#3b8ed0", outline="")
        self._playhead_id = self.canvas.create_line(0, 0, 0, height, fill="#e74c3c", width=2)
        self._update_playhead()

    def _update_playhead(self) -> None:
        if self._playhead_id is None:
            return
        width = max(self._cached_width, 1)
        height = max(self._cached_height, 1)
        ratio = 0.0 if self._duration <= 0 else max(0.0, min(1.0, self._position / self._duration))
        pos_x = int(ratio * width)
        self.canvas.coords(self._playhead_id, pos_x, 0, pos_x, height)

    @staticmethod
    def _compute_base_envelope(audio: np.ndarray, target_points: int = 4096) -> np.ndarray:
        if audio.size == 0:
            return np.array([], dtype=np.float32)
        absolute = np.abs(np.asarray(audio, dtype=np.float32))
        points = max(1, min(int(target_points), int(absolute.size)))
        if absolute.size <= points:
            return absolute.astype(np.float32)

        chunk_size = max(1, absolute.size // points)
        trimmed = absolute[: chunk_size * points]
        chunks = trimmed.reshape(points, chunk_size)
        return np.max(chunks, axis=1).astype(np.float32)

    @staticmethod
    def _resample_envelope(envelope: np.ndarray, target_points: int) -> np.ndarray:
        if target_points <= 0:
            return np.array([], dtype=np.float32)
        if envelope.size == 0:
            return np.zeros(target_points, dtype=np.float32)
        if envelope.size == target_points:
            return envelope.astype(np.float32, copy=False)
        if envelope.size == 1:
            return np.full(target_points, float(envelope[0]), dtype=np.float32)

        source_axis = np.linspace(0.0, 1.0, num=envelope.size, dtype=np.float32)
        target_axis = np.linspace(0.0, 1.0, num=target_points, dtype=np.float32)
        return np.interp(target_axis, source_axis, envelope).astype(np.float32)
