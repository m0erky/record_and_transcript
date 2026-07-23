"""Implementation eines whisper.cpp-Backends."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import requests

from app.backends.base import (
    BackendConfigurationError,
    TranscriptSegment,
    TranscriptionResult,
    TranscriptionBackend,
)


LOGGER = logging.getLogger(__name__)


_MODEL_DOWNLOAD_BASE_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/"
_MODEL_FILES: dict[str, str] = {
    "tiny": "ggml-tiny.bin",
    "base": "ggml-base.bin",
    "small": "ggml-small.bin",
}


@dataclass(frozen=True)
class WhisperCppConfig:
    model_cache_dir: Path | None = None
    use_vulkan: bool = True
    vulkan_device: str | None = None
    auto_download_models: bool = True
    download_timeout: float = 60.0


class WhisperCppBackend(TranscriptionBackend):
    MODEL_SIZES: tuple[str, ...] = ("tiny", "base", "small")
    EXECUTION_MODES: tuple[str, ...] = ("auto", "cpu", "vulkan")

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        super().__init__(config=config)
        options = config or {}
        cache_dir = options.get("model_cache_dir")
        if cache_dir is not None:
            cache_dir = Path(cache_dir)
        auto_download_models = bool(options.get("auto_download_models", True))
        download_timeout = float(options.get("download_timeout", 60.0))
        self._impl_config = WhisperCppConfig(
            model_cache_dir=cache_dir,
            use_vulkan=bool(options.get("use_vulkan", True)),
            vulkan_device=options.get("vulkan_device"),
            auto_download_models=auto_download_models,
            download_timeout=download_timeout,
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
            auto_download_models=self._impl_config.auto_download_models,
            download_timeout=self._impl_config.download_timeout,
        )
        self._impl_config.model_cache_dir.mkdir(parents=True, exist_ok=True)
        if self._impl_config.use_vulkan:
            self._prepare_vulkan()
        if shutil.which(str(self._binary_path)) is None and not self._binary_path.exists():
            raise BackendConfigurationError(
                f"Whisper.cpp-Binary '{self._binary_path}' ist nicht vorhanden oder ausführbar."
            )
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
        text = ""
        segments: list[TranscriptSegment] = []
        existing_names = {child.name for child in output_dir.iterdir()}
        try:
            model_path = self._ensure_model_path_for_size(model_size)
            prefix = output_dir / temp_wave.stem
            cmd = self._build_command(prefix, temp_wave, language, model_path, execution_mode)
            if on_progress:
                on_progress("Whisper.cpp wird gestartet...")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:  # pragma: no cover - runtime failure
            message = exc.stderr.strip() if exc.stderr else str(exc)
            raise RuntimeError("Whisper.cpp ist fehlgeschlagen: %s" % message) from exc
        else:
            transcript_path = self._select_output_file(output_dir, existing_names, ".txt")
            text = self._load_transcript_text(transcript_path)
            segments = self._parse_segment_file(self._select_output_file(output_dir, existing_names, ".srt", required=False))
        finally:
            temp_wave.unlink(missing_ok=True)
            shutil.rmtree(output_dir, ignore_errors=True)
        if on_progress:
            on_progress("Whisper.cpp Transkription abgeschlossen.")
        return TranscriptionResult(
            text=text.strip(),
            language=language or "auto",
            duration=len(audio) / sample_rate,
            segments=segments,
        )

    def cleanup(self) -> None:
        self._initialized = False

    def _write_audio_to_file(self, audio: np.ndarray, sample_rate: int) -> Path:
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        temp_file = Path(path)
        try:
            import soundfile as sf
        except ImportError:  # pragma: no cover - optional dependency missing
            from scipy.io import wavfile as scipy_wavfile

            adjusted = np.clip(audio, -1.0, 1.0)
            scaled = (adjusted * np.iinfo(np.int16).max).astype(np.int16)
            scipy_wavfile.write(str(temp_file), sample_rate, scaled)
        else:
            sf.write(str(temp_file), audio, sample_rate, format="WAV", subtype="PCM_16")
        return temp_file

    def _build_command(
        self,
        output_prefix: Path,
        wave_path: Path,
        language: str | None,
        model_path: Path,
        execution_mode: str,
    ) -> list[str]:
        cmd = [
            str(self._binary_path),
            "-m",
            str(model_path),
            "-f",
            str(wave_path),
            "-o",
            str(output_prefix),
            "-otxt",
            "-osrt",
            "-t",
            str(self._threads),
        ]
        if language and language.lower() != "auto":
            cmd.extend(["-l", language])
        if self._translate:
            cmd.append("--translate")
        if self._word_timestamps:
            cmd.append("--word_timestamps")
        exec_mode = (execution_mode or "auto").lower()
        if exec_mode == "vulkan":
            cmd.append("--vulkan")
            if self._impl_config.vulkan_device:
                cmd.extend(["--vulkan-device", self._impl_config.vulkan_device])
        elif exec_mode not in ("auto", "cpu"):
            raise BackendConfigurationError(
                f"Unbekannter Whisper.cpp-Ausführungsmodus: {execution_mode!r}"
            )
        return cmd

    def _model_file_name(self, model_size: str) -> str:
        try:
            return _MODEL_FILES[model_size]
        except KeyError as exc:
            raise BackendConfigurationError(
                f"Whisper.cpp unterstützt das Modell '{model_size}' nicht."
            ) from exc

    def _model_download_url(self, model_size: str) -> str:
        return _MODEL_DOWNLOAD_BASE_URL + self._model_file_name(model_size)

    def _ensure_model_path_for_size(self, model_size: str) -> Path:
        if self._model_path is not None:
            return self._model_path
        normalized = model_size.lower()
        model_dir = self._impl_config.model_cache_dir
        if model_dir is None:
            raise BackendConfigurationError("Kein Speicherort für Whisper.cpp-Modelle definiert.")
        file_name = self._model_file_name(normalized)
        candidate = model_dir / file_name
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
        if not self._impl_config.auto_download_models:
            raise BackendConfigurationError(
                f"Whisper.cpp-Modell '{normalized}' wurde nicht gefunden. "
                "Setze 'model_path' oder aktiviere den automatischen Download."
            )
        self._download_model(normalized, candidate)
        return candidate

    def _download_model(self, model_size: str, destination: Path) -> None:
        url = self._model_download_url(model_size)
        LOGGER.info("Lade Whisper.cpp-Modell '%s' herunter: %s", model_size, url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_destination = destination.with_suffix(destination.suffix + ".part")
        response = None
        try:
            response = requests.get(url, stream=True, timeout=self._impl_config.download_timeout)
            response.raise_for_status()
            with temp_destination.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=32 * 1024):
                    if chunk:
                        handle.write(chunk)
        except requests.RequestException as exc:
            temp_destination.unlink(missing_ok=True)
            raise RuntimeError(
                f"Whisper.cpp-Modell '{model_size}' konnte nicht heruntergeladen werden: {exc}"
            ) from exc
        finally:
            if response is not None:
                response.close()
        temp_destination.replace(destination)

    def _load_transcript_text(self, path: Path) -> str:
        if not path.exists():
            raise RuntimeError(f"Whisper.cpp-Ausgabedatei {path} wurde nicht erzeugt.")
        return path.read_text(encoding="utf-8")

    def _parse_segment_file(self, path: Path | None) -> list[TranscriptSegment]:
        if path is None or not path.exists():
            return []
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        segments: list[TranscriptSegment] = []
        blocks = re.split(r"\n\s*\n", content)
        for block in blocks:
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if len(lines) < 3:
                continue
            time_line = lines[1]
            try:
                start_str, end_str = [part.strip() for part in time_line.split("-->")]
            except ValueError:
                continue
            text = " ".join(lines[2:])
            try:
                start = self._srt_timestamp_to_seconds(start_str)
                end = self._srt_timestamp_to_seconds(end_str)
            except ValueError:
                continue
            segments.append(TranscriptSegment(start=start, end=end, text=text))
        return segments

    def _select_output_file(self, output_dir: Path, existing_names: set[str], suffix: str, required: bool = True) -> Path | None:
        candidates = [child for child in output_dir.iterdir() if child.suffix.lower() == suffix.lower() and child.name not in existing_names]
        if not candidates:
            candidates = [child for child in output_dir.iterdir() if child.suffix.lower() == suffix.lower()]
        if not candidates:
            if required:
                raise RuntimeError(f"Keine Whisper.cpp-Ausgabedatei mit Endung '{suffix}' gefunden.")
            return None
        return max(candidates, key=lambda child: child.stat().st_mtime)

    def _srt_timestamp_to_seconds(self, timestamp: str) -> float:
        timestamp = timestamp.strip()
        parts = timestamp.split(":")
        if len(parts) != 3:
            raise ValueError(f"Ungültiges Zeitformat: {timestamp}")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_part = parts[2]
        seconds_str, milliseconds_str = seconds_part.split(",")
        seconds = int(seconds_str)
        milliseconds = int(milliseconds_str)
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0

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
