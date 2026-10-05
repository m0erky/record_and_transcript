"""Azure OpenAI Speech-to-Text-Backend."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import numpy as np
import requests

from app.backends.base import TranscriptionBackend, TranscriptionResult


@dataclass(frozen=True)
class AzureOpenAIApiConfig:
    endpoint: str | None
    api_key: str | None
    deployment: str | None
    api_version: str | None
    timeout: int


class AzureOpenAIBackend(TranscriptionBackend):
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
        self._api_config = AzureOpenAIApiConfig(
            endpoint=options.get("endpoint"),
            api_key=options.get("api_key"),
            deployment=options.get("deployment"),
            api_version=options.get("api_version", "2023-05-15"),
            timeout=int(options.get("timeout", 120)),
        )
        self._initialized = False
        self._headers: Mapping[str, str] | None = None

    def initialize(self) -> None:
        self._ensure_configuration()
        self._headers = self._build_headers()
        self._initialized = True

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
        if not self._initialized:
            self.initialize()
        if speaker_diarization and model_size not in self._DIARIZE_MODELS:
            raise ValueError("Für Sprecher-Diarisierung wird ein Modell mit Diarize-Suffix benötigt.")
        if on_progress:
            on_progress("Audio wird an Azure OpenAI gesendet...")
        buffer = self._audio_to_wav(audio, sample_rate)
        response = self._post_transcription(buffer, language, model_size, speaker_diarization)
        if on_progress:
            on_progress("Antwort von Azure OpenAI empfangen.")
        payload = response.json()
        text = payload.get("text") or payload.get("transcript") or ""
        language_used = payload.get("language") or (language or "auto")
        return TranscriptionResult(
            text=text.strip(),
            language=language_used,
            duration=len(audio) / sample_rate,
        )

    def cleanup(self) -> None:
        self._initialized = False
        self._headers = None

    def _ensure_configuration(self) -> None:
        if not self._api_config.endpoint:
            raise RuntimeError("Azure-Endpoint fehlt in den Backend-Einstellungen.")
        if not self._api_config.api_key:
            raise RuntimeError("Azure API-Key fehlt in den Backend-Einstellungen.")
        if not self._api_config.deployment:
            raise RuntimeError("Azure Deployment-Name fehlt in den Backend-Einstellungen.")

    def _build_headers(self) -> Mapping[str, str]:
        return {
            "api-key": self._api_config.api_key,  # type: ignore[arg-type]
        }

    def _transcription_url(self) -> str:
        base = self._api_config.endpoint.rstrip("/")
        return (
            f"{base}/openai/deployments/{self._api_config.deployment}/audio/transcriptions"
            f"?api-version={self._api_config.api_version}"
        )

    def _audio_to_wav(self, audio: np.ndarray, sample_rate: int) -> io.BytesIO:
        try:
            import soundfile as sf
        except ImportError as exc:  # pragma: no cover - missing dependency
            raise RuntimeError("Das Paket 'soundfile' wird für Azure OpenAI benötigt.") from exc
        buffer = io.BytesIO()
        sf.write(buffer, audio, samplerate=sample_rate, format="WAV", subtype="PCM_16")
        buffer.seek(0)
        return buffer

    def _post_transcription(
        self,
        buffer: io.BytesIO,
        language: str | None,
        model_size: str,
        speaker_diarization: bool,
    ) -> requests.Response:
        files = {"file": ("audio.wav", buffer, "audio/wav")}
        data: dict[str, str] = {
            "language": language or "de",
            "response_format": "text",
            "model": model_size,
        }
        if speaker_diarization:
            data["diarize"] = "true"
        url = self._transcription_url()
        if self._headers is None:
            raise RuntimeError("Azure OpenAI Backend wurde nicht initialisiert.")
        response = requests.post(
            url,
            headers=self._headers,
            data=data,
            files=files,
            timeout=self._api_config.timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Azure OpenAI Transkription fehlgeschlagen: {response.status_code} {response.text}"
            )
        return response

    @classmethod
    def supports_gpu(cls) -> bool:
        return False

    @classmethod
    def supports_diarization(cls) -> bool:
        return bool(cls._DIARIZE_MODELS)

    @classmethod
    def supports_vad(cls) -> bool:
        return False


__all__ = ["AzureOpenAIBackend"]
