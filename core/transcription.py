"""Gemeinsame Typen und Basisschnittstelle für Transkriptions-Backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class SpeechRegion:
    start: float
    end: float
    speaker_label: int | None = None


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None


@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration: float
    segments: list[TranscriptSegment] = field(default_factory=list)


class TranscriptionBackend(ABC):
    """Schnittstelle für austauschbare Transkriptions-Backends."""

    MODEL_SIZES: tuple[str, ...] = ()
    EXECUTION_MODES: tuple[str, ...] = ()

    @classmethod
    def available_model_sizes(cls) -> list[str]:
        return list(cls.MODEL_SIZES)

    @classmethod
    def available_execution_modes(cls) -> list[str]:
        return list(cls.EXECUTION_MODES)

    @classmethod
    def cuda_diagnostic_report(cls) -> str:
        return "Diagnostics are not supported for this backend."

    @abstractmethod
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
        """Transkribiere das gegebene Audiosignal."""
        raise NotImplementedError("Transcription backend must implement 'transcribe' method.")


__all__ = [
    "SpeechRegion",
    "TranscriptSegment",
    "TranscriptionResult",
    "TranscriptionBackend",
]
