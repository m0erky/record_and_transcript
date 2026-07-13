"""Audio-Wiedergabe mit Play, Pause und Spulen."""

from __future__ import annotations

import threading
from typing import Callable

import numpy as np
import sounddevice as sd


class AudioPlayer:
    def __init__(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self._audio = np.array([], dtype=np.float32)
        self._position = 0
        self._playing = False
        self._paused = False
        self._stream: sd.OutputStream | None = None
        self._lock = threading.Lock()
        self._on_position_change: Callable[[float, float], None] | None = None
        self._on_finished: Callable[[], None] | None = None

    @property
    def duration(self) -> float:
        if self._audio.size == 0:
            return 0.0
        return len(self._audio) / self.sample_rate

    @property
    def position(self) -> float:
        return self._position / self.sample_rate

    @property
    def is_playing(self) -> bool:
        return self._playing and not self._paused

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def has_audio(self) -> bool:
        return self._audio.size > 0

    def set_callbacks(
        self,
        on_position_change: Callable[[float, float], None] | None = None,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        self._on_position_change = on_position_change
        self._on_finished = on_finished

    def load(self, audio: np.ndarray) -> None:
        self.stop()
        self._audio = audio.astype(np.float32).copy()
        self._position = 0
        self._notify_position()

    def play(self) -> None:
        if self._audio.size == 0:
            return

        with self._lock:
            if self._playing and self._paused:
                self._paused = False
                self._start_stream()
                return

            if self._playing:
                return

            if self._position >= len(self._audio):
                self._position = 0

            self._playing = True
            self._paused = False
            self._start_stream()

    def pause(self) -> None:
        with self._lock:
            if not self._playing or self._paused:
                return
            self._paused = True
            self._close_stream()

    def stop(self) -> None:
        with self._lock:
            self._playing = False
            self._paused = False
            self._close_stream()
            self._position = 0
            self._notify_position()

    def seek(self, seconds: float) -> None:
        if self._audio.size == 0:
            return

        was_playing = self.is_playing
        if self._playing:
            with self._lock:
                self._playing = False
                self._paused = False
                self._close_stream()

        clamped = max(0.0, min(seconds, self.duration))
        self._position = int(clamped * self.sample_rate)
        self._notify_position()

        if was_playing:
            self.play()

    def skip(self, delta_seconds: float) -> None:
        self.seek(self.position + delta_seconds)

    def _close_stream(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _start_stream(self) -> None:
        self._close_stream()

        def callback(outdata: np.ndarray, frames: int, _time, status) -> None:
            if status:
                print(f"Wiedergabe-Status: {status}")

            with self._lock:
                if not self._playing or self._paused:
                    outdata.fill(0)
                    raise sd.CallbackStop()

                end = self._position + frames
                chunk = self._audio[self._position:end]

                if chunk.size == 0:
                    outdata.fill(0)
                    self._playing = False
                    self._notify_position()
                    if self._on_finished:
                        self._on_finished()
                    raise sd.CallbackStop()

                if chunk.size < frames:
                    outdata[: chunk.size, 0] = chunk
                    outdata[chunk.size :, 0] = 0
                    self._position = len(self._audio)
                    self._playing = False
                    self._notify_position()
                    if self._on_finished:
                        self._on_finished()
                    raise sd.CallbackStop()

                outdata[:, 0] = chunk
                self._position = end
                self._notify_position()

        self._stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=callback,
        )
        self._stream.start()

    def _notify_position(self) -> None:
        if self._on_position_change:
            self._on_position_change(self.position, self.duration)
