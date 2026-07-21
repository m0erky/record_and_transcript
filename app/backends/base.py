"""Gemeinsame Typen und Schnittstelle für Transkriptions-Backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np


class BackendConfigurationError(RuntimeError):
    """Raised when a transcription backend cannot be configured."""
    pass


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
    """Basisschnittstelle für austauschbare Transkriptions-Backends."""

    MODEL_SIZES: tuple[str, ...] = ()
    EXECUTION_MODES: tuple[str, ...] = ("cpu",)

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}

    def initialize(self) -> None:
        """Bereite das Backend vor (z. B. Modell laden)."""
        return None

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
        raise NotImplementedError("Transcription backend must implement 'transcribe'.")

    @classmethod
    def get_available_models(cls) -> list[str]:
        return list(cls.MODEL_SIZES)

    @classmethod
    def available_execution_modes(cls) -> list[str]:
        return list(cls.EXECUTION_MODES)

    @classmethod
    def supports_gpu(cls) -> bool:
        return False

    @classmethod
    def supports_diarization(cls) -> bool:
        return False

    @classmethod
    def supports_vad(cls) -> bool:
        return False

    def cleanup(self) -> None:
        """Räume genutzte Ressourcen auf."""
        return None


__all__ = [
    "BackendConfigurationError",
    "SpeechRegion",
    "TranscriptSegment",
    "TranscriptionResult",
    "TranscriptionBackend",
]
