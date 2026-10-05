"""Stub für ein OpenAI Speech-to-Text-Backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import numpy as np

from app.backends.base import TranscriptionBackend, TranscriptionResult


@dataclass(frozen=True)
class OpenAIApiConfig:
    api_key: str | None
    base_url: str
    organization: str | None
    timeout: int


class OpenAIBackend(TranscriptionBackend):
    MODEL_SIZES: tuple[str, ...] = (
        "gpt-4o-mini-transcribe",
        "gpt-4o-transcribe",
        "gpt-4o-transcribe-diarize",
        "whisper-1",
    )
    EXECUTION_MODES: tuple[str, ...] = ("cpu", "auto")
    _DIARIZE_MODELS = {"gpt-4o-transcribe-diarize"}

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        super().__init__(config=config)
        options = self._config
        self._api_config = OpenAIApiConfig(
            api_key=options.get("api_key") or os.environ.get("OPENAI_API_KEY"),
            base_url=options.get("base_url", "https://api.openai.com"),
            organization=options.get("organization"),
            timeout=int(options.get("timeout", 120)),
        )
        self._session_initialized = False
        self._headers: Mapping[str, str] | None = None

    def initialize(self) -> None:
        self._validate_api_key()
        self._headers = self._build_headers()
        self._session_initialized = True

    def transcribe(
        self,
        audio: np.ndarray,
        *,
        sample_rate: int = 16_000,
        model_size: str = "gpt-4o-mini-transcribe",
        language: str | None = "de",
        execution_mode: str = "auto",
        speaker_diarization: bool = False,
        max_speakers: int = 2,
        on_progress: Callable[[str], None] | None = None,
    ) -> TranscriptionResult:
        raise NotImplementedError(
            "OpenAIBackend ist aktuell noch nicht implementiert. TODO: API-Integration einbauen."
        )

    def cleanup(self) -> None:
        self._session_initialized = False
        self._headers = None

    def _validate_api_key(self) -> None:
        if not self._api_config.api_key:
            raise RuntimeError(
                "OpenAI API-Key fehlt. Bitte in den Einstellungen oder über OPENAI_API_KEY setzen."
            )

    def _build_headers(self) -> Mapping[str, str]:
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._api_config.api_key}",
            "Content-Type": "application/json",
        }
        if self._api_config.organization:
            headers["OpenAI-Organization"] = self._api_config.organization
        return headers

    @classmethod
    def supports_gpu(cls) -> bool:
        return False

    @classmethod
    def supports_diarization(cls) -> bool:
        return bool(cls._DIARIZE_MODELS)

    @classmethod
    def supports_vad(cls) -> bool:
        return False


__all__ = ["OpenAIBackend"]
