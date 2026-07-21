"""Schnittstelle zu den Transkriptions-Backends."""

from __future__ import annotations

from .faster_whisper_backend import FasterWhisperBackend
from .whisper_cpp_backend import WhisperCppBackend
from .openai_backend import OpenAIBackend
from .azure_openai_backend import AzureOpenAIBackend

__all__ = [
    "FasterWhisperBackend",
    "WhisperCppBackend",
    "OpenAIBackend",
    "AzureOpenAIBackend",
]
