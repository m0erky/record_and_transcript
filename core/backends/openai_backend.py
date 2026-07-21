"""Stub für ein OpenAI Whisper-Backend."""

from __future__ import annotations

from typing import Callable

import numpy as np

from core.transcription import TranscriptionBackend, TranscriptionResult


class OpenAIBackend(TranscriptionBackend):
    MODEL_SIZES: tuple[str, ...] = ()
    EXECUTION_MODES: tuple[str, ...] = ("cpu", "auto")

    def transcribe(
        self,
        audio: np.ndarray,
        *,
        sample_rate: int = 16_000,
        model_size: str = "small",
        language: str | None = "de",
        execution_mode: str = "auto",
        speaker_diarization: bool = False,
        max_speakers: int = 2,
        on_progress: Callable[[str], None] | None = None,
    ) -> TranscriptionResult:
        raise NotImplementedError("OpenAIBackend is not implemented yet.")


__all__ = ["OpenAIBackend"]
