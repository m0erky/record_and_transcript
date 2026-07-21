"""Factory zum Erzeugen eines Transkriptions-Backends anhand der Konfiguration."""

from __future__ import annotations

from typing import Any

from .azure_openai_backend import AzureOpenAIBackend
from .faster_whisper_backend import FasterWhisperBackend
from .openai_backend import OpenAIBackend
from .whisper_cpp_backend import WhisperCppBackend
from core.transcription import TranscriptionBackend


class TranscriptionBackendFactory:
    DEFAULT_BACKEND = "faster_whisper"
    _BACKENDS: dict[str, type[TranscriptionBackend]] = {
        "faster_whisper": FasterWhisperBackend,
        "whisper_cpp": WhisperCppBackend,
        "openai": OpenAIBackend,
        "azure_openai": AzureOpenAIBackend,
    }

    def __init__(self, *, default_backend: str | None = None) -> None:
        self._default_backend = default_backend or self.DEFAULT_BACKEND

    def create_backend(self, config: dict[str, Any] | None = None) -> TranscriptionBackend:
        key = self._backend_key(config)
        backend_cls = self._BACKENDS.get(key)
        if backend_cls is None:
            raise ValueError(f"Unbekanntes Transkriptions-Backend: {key}")
        return backend_cls()

    def available_backends(self) -> list[str]:
        return list(self._BACKENDS.keys())

    def _backend_key(self, config: dict[str, Any] | None) -> str:
        if config is None:
            return self._default_backend
        backend = config.get("backend")
        if backend:
            return backend
        return self._default_backend


__all__ = ["TranscriptionBackendFactory"]
