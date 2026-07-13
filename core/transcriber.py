"""Whisper-Transkription mit faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from faster_whisper import WhisperModel


@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration: float


class WhisperTranscriber:
    MODEL_SIZES = ("tiny", "base", "small", "medium")

    def __init__(self) -> None:
        self._model: WhisperModel | None = None
        self._loaded_size: str | None = None

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16_000,
        model_size: str = "small",
        language: str | None = "de",
        on_progress: Callable[[str], None] | None = None,
    ) -> TranscriptionResult:
        if audio.size == 0:
            raise ValueError("Keine Audiodaten zum Transkribieren vorhanden.")

        if on_progress:
            on_progress("Whisper-Modell wird geladen...")

        self._ensure_model(model_size, on_progress)

        if on_progress:
            on_progress("Transkription läuft...")

        segments, info = self._model.transcribe(
            audio,
            language=None if language == "auto" else language,
            beam_size=5,
            vad_filter=True,
        )

        text_parts: list[str] = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        full_text = " ".join(part for part in text_parts if part).strip()
        duration = len(audio) / sample_rate

        return TranscriptionResult(
            text=full_text,
            language=info.language or (language or "auto"),
            duration=duration,
        )

    def _ensure_model(
        self,
        model_size: str,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        if self._model is not None and self._loaded_size == model_size:
            return

        if on_progress:
            on_progress(f"Modell '{model_size}' wird heruntergeladen/geladen...")

        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self._loaded_size = model_size
