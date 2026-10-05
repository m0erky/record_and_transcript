from __future__ import annotations

from .base import (
    SpeechRegion,
    TranscriptSegment,
    TranscriptionBackend,
    TranscriptionResult,
)
from .factory import BackendFactory
from .faster_whisper_backend import FasterWhisperBackend
from .openai_backend import OpenAIBackend
from .azure_openai_backend import AzureOpenAIBackend
from .whisper_cpp_backend import WhisperCppBackend

__all__ = [
    "BackendFactory",
    "FasterWhisperBackend",
    "WhisperCppBackend",
    "OpenAIBackend",
    "AzureOpenAIBackend",
    "SpeechRegion",
    "TranscriptSegment",
    "TranscriptionBackend",
    "TranscriptionResult",
]
