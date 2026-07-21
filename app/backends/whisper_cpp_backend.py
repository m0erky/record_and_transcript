"""Stub für ein zukünftiges whisper.cpp-Backend."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np

from app.backends.base import TranscriptionBackend, TranscriptionResult


class WhisperCppBackend(TranscriptionBackend):
    MODEL_SIZES: tuple[str, ...] = ("tiny", "base", "small")
    EXECUTION_MODES: tuple[str, ...] = ("cpu", "vulkan")

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        super().__init__(config=config)
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

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
        raise NotImplementedError("WhisperCppBackend ist derzeit noch nicht implementiert.")

    @classmethod
    def supports_gpu(cls) -> bool:
        return True

    def cleanup(self) -> None:
        self._initialized = False


__all__ = ["WhisperCppBackend"]
