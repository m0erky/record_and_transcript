"""Factory zum Erzeugen eines Transkriptions-Backends anhand der Konfiguration."""

from __future__ import annotations

from typing import Any

from app.backends.base import TranscriptionBackend
from app.backends.azure_openai_backend import AzureOpenAIBackend
from app.backends.faster_whisper_backend import FasterWhisperBackend
from app.backends.openai_backend import OpenAIBackend
from app.backends.whisper_cpp_backend import WhisperCppBackend


class BackendFactory:
    DEFAULT_BACKEND = "faster_whisper"
    _BACKENDS: dict[str, type[TranscriptionBackend]] = {
        "faster_whisper": FasterWhisperBackend,
        "whispercpp": WhisperCppBackend,
        "whisper_cpp": WhisperCppBackend,
        "openai": OpenAIBackend,
        "azure_openai": AzureOpenAIBackend,
        "azure-openai": AzureOpenAIBackend,
    }

    def __init__(self, *, default_backend: str | None = None) -> None:
        self._default_backend = default_backend or self.DEFAULT_BACKEND

    def create_backend(self, config: dict[str, Any] | None = None) -> TranscriptionBackend:
        key = self._backend_key(config)
        backend_cls = self._BACKENDS.get(key)
        if backend_cls is None:
            raise ValueError(f"Unbekanntes Transkriptions-Backend: {key}")
        options = (config or {}).get("options") or {}
        return backend_cls(config=options)

    def available_backends(self) -> list[str]:
        return list(self._BACKENDS.keys())

    def _backend_key(self, config: dict[str, Any] | None) -> str:
        if config is None:
            return self._default_backend
        backend = config.get("backend")
        if backend:
            return backend
        return self._default_backend


__all__ = ["BackendFactory"]
