"""Implementation eines whisper.cpp-Backends."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import soundfile as sf

from app.backends.base import BackendConfigurationError, TranscriptionBackend, TranscriptionResult


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WhisperCppConfig:
    model_cache_dir: Path | None = None
    use_vulkan: bool = True
    vulkan_device: str | None = None


class WhisperCppBackend(TranscriptionBackend):
    MODEL_SIZES: tuple[str, ...] = ("tiny", "base", "small")
    EXECUTION_MODES: tuple[str, ...] = ("cpu", "vulkan")

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        super().__init__(config=config)
        options = config or {}
        cache_dir = options.get("model_cache_dir")
        if cache_dir is not None:
            cache_dir = Path(cache_dir)
        self._impl_config = WhisperCppConfig(
            model_cache_dir=cache_dir,
            use_vulkan=bool(options.get("use_vulkan", True)),
            vulkan_device=options.get("vulkan_device"),
        )
        self._binary_path = Path(options.get("binary_path", "main"))
        self._model_path = Path(options.get("model_path")) if options.get("model_path") else None
        self._threads = max(1, int(options.get("threads", 2)))
        self._translate = bool(options.get("translate", False))
        self._word_timestamps = bool(options.get("word_timestamps", False))
        self._initialized = False

    def initialize(self) -> None:
        cache_dir = self._impl_config.model_cache_dir or Path("./models/whisper_cpp")
        self._impl_config = WhisperCppConfig(
            model_cache_dir=cache_dir,
            use_vulkan=self._impl_config.use_vulkan,
            vulkan_device=self._impl_config.vulkan_device,
        )
        self._impl_config.model_cache_dir.mkdir(parents=True, exist_ok=True)
        if self._impl_config.use_vulkan:
            self._prepare_vulkan()
        if self._model_path is None:
            raise BackendConfigurationError("Whisper.cpp Modell fehlt in den Backend-Einstellungen ('model_path').")
        if not self._model_path.exists():
            raise BackendConfigurationError(f"Whisper.cpp Modell '{self._model_path}' wurde nicht gefunden.")
        if shutil.which(str(self._binary_path)) is None and not self._binary_path.exists():
            raise RuntimeError(f"Whisper.cpp-Binary '{self._binary_path}' ist nicht vorhanden oder nicht ausführbar.")
        self._initialized = True

    def _prepare_vulkan(self) -> None:
        if self._impl_config.vulkan_device:
            LOGGER.debug("Vulkan-Device vorgesehen: %s", self._impl_config.vulkan_device)

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
        if not self._initialized:
            self.initialize()
        if speaker_diarization:
            raise NotImplementedError("Whisper.cpp unterstützt aktuell keine Sprecher-Diarisierung über das CLI.")
        temp_wave = self._write_audio_to_file(audio, sample_rate)
        output_dir = Path(tempfile.mkdtemp(prefix="whispercpp_"))
        try:
            cmd = self._build_command(temp_wave, output_dir, language, model_size, execution_mode)
            if on_progress:
                on_progress("Whisper.cpp wird gestartet...")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            transcript_path = self._transcript_path(output_dir, temp_wave)
            text = self._load_transcript_text(transcript_path)
        finally:
            temp_wave.unlink(missing_ok=True)
            shutil.rmtree(output_dir, ignore_errors=True)
        if on_progress:
            on_progress("Whisper.cpp Transkription abgeschlossen.")
        return TranscriptionResult(
            text=text.strip(),
            language=language or "auto",
            duration=len(audio) / sample_rate,
            segments=[],
        )

    def cleanup(self) -> None:
        self._initialized = False

    def _write_audio_to_file(self, audio: np.ndarray, sample_rate: int) -> Path:
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        temp_file = Path(path)
        sf.write(str(temp_file), audio, sample_rate, format="WAV", subtype="PCM_16")
        return temp_file

    def _build_command(
        self,
        wave_path: Path,
        output_dir: Path,
        language: str | None,
        model_size: str,
        execution_mode: str,
    ) -> list[str]:
        cmd = [
            str(self._binary_path),
            "-m",
            str(self._model_path),
            "-f",
            str(wave_path),
            "-o",
            str(output_dir),
            "-otxt",
            "-t",
            str(self._threads),
        ]
        if language and language.lower() != "auto":
            cmd.extend(["-l", language])
        if self._translate:
            cmd.append("--translate")
        if self._word_timestamps:
            cmd.append("--word_timestamps")
        if execution_mode.lower() == "vulkan":
            cmd.append("--vulkan")
            if self._impl_config.vulkan_device:
                cmd.extend(["--vulkan-device", self._impl_config.vulkan_device])
        return cmd

    def _transcript_path(self, output_dir: Path, wave_path: Path) -> Path:
        return output_dir / f"{wave_path.name}.txt"

    def _load_transcript_text(self, path: Path) -> str:
        if not path.exists():
            raise RuntimeError(f"Whisper.cpp-Ausgabedatei {path} wurde nicht erzeugt.")
        return path.read_text(encoding="utf-8")

    @classmethod
    def supports_gpu(cls) -> bool:
        return True

    @classmethod
    def supports_diarization(cls) -> bool:
        return False

    @classmethod
    def supports_vad(cls) -> bool:
        return False


__all__ = ["WhisperCppBackend"]
