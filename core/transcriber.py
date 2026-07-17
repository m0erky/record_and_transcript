"""Whisper-Transkription mit optionaler Sprecher-Unterscheidung."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
from faster_whisper import WhisperModel
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.fftpack import dct
from scipy.signal import spectrogram
from scipy.spatial.distance import pdist, squareform

try:
    import ctranslate2
except ImportError:
    ctranslate2 = None


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


class WhisperTranscriber:
    MODEL_SIZES = ("tiny", "base", "small", "medium")
    EXECUTION_MODES = ("auto", "cpu", "cuda")
    _registered_dll_directories: set[str] = set()
    _dll_directory_handles: list[object] = []

    def __init__(self) -> None:
        self._ensure_windows_cuda_runtime_paths()
        self._model: WhisperModel | None = None
        self._loaded_config: tuple[str, str, str] | None = None

    @classmethod
    def _ensure_windows_cuda_runtime_paths(cls) -> None:
        if sys.platform != "win32":
            return

        def _prepend_to_path(directory: Path) -> None:
            resolved = str(directory.resolve(strict=False))
            current_path = os.environ.get("PATH", "")
            parts = [part for part in current_path.split(os.pathsep) if part]
            if any(part.lower() == resolved.lower() for part in parts):
                return
            os.environ["PATH"] = os.pathsep.join([resolved, *parts]) if parts else resolved

        def _register(directory: Path) -> None:
            resolved = directory.resolve(strict=False)
            if not resolved.is_dir():
                return
            key = str(resolved).lower()
            if key in cls._registered_dll_directories:
                _prepend_to_path(resolved)
                return
            if hasattr(os, "add_dll_directory"):
                try:
                    handle = os.add_dll_directory(str(resolved))
                except OSError:
                    handle = None
                else:
                    cls._dll_directory_handles.append(handle)
            cls._registered_dll_directories.add(key)
            _prepend_to_path(resolved)

        candidates: list[Path] = []
        env_keys = ("CUDA_PATH", "CUDA_HOME", "NVIDIA_CUDA_PATH", "CUDA_BIN_PATH")
        for env_key in env_keys:
            value = os.environ.get(env_key)
            if value:
                candidate = Path(value)
                candidates.append(candidate if candidate.name.lower() == "bin" else candidate / "bin")
        for env_key, value in os.environ.items():
            if env_key.startswith("CUDA_PATH") and value:
                candidate = Path(value)
                candidates.append(candidate if candidate.name.lower() == "bin" else candidate / "bin")
        for root_key in ("ProgramFiles", "ProgramFiles(x86)"):
            root_value = os.environ.get(root_key)
            if not root_value:
                continue
            cuda_root = Path(root_value) / "NVIDIA GPU Computing Toolkit" / "CUDA"
            if cuda_root.exists():
                candidates.extend(cuda_root.glob("*/bin"))

        for candidate in candidates:
            _register(candidate)

    @classmethod
    def _is_dll_load_error(cls, exc: Exception) -> bool:
        message = str(exc).lower()
        return any(token in message for token in ("dll", "cannot be loaded", "could not be loaded", "loadlibrary", "not found"))

    @classmethod
    def _cuda_device_issue(cls) -> str | None:
        if ctranslate2 is None:
            return "CTranslate2 ist nicht installiert."
        try:
            count = ctranslate2.get_cuda_device_count()
        except Exception as exc:
            return f"CUDA-Geräteprüfung fehlgeschlagen: {exc}"
        return None if count > 0 else "Es wurde keine CUDA-fähige GPU für Whisper gefunden."

    @classmethod
    def _cuda_model_smoke_test_issue(cls) -> str | None:
        cls._ensure_windows_cuda_runtime_paths()
        issue = cls._cuda_device_issue()
        if issue:
            return issue
        try:
            model = WhisperModel("tiny", device="cuda", compute_type="float16", local_files_only=True)
        except Exception as exc:
            low = str(exc).lower()
            if any(token in low for token in ("local_files_only", "local files only", "no such file", "not found", "cache", "download")):
                return f"Der CUDA-Modelltest konnte nicht ausgeführt werden, weil das lokale 'tiny'-Modell nicht im Cache gefunden wurde: {exc}"
            return f"Whisper-Modelltest auf CUDA fehlgeschlagen: {exc}"
        actual_device = getattr(getattr(model, "model", None), "device", None)
        return None if actual_device == "cuda" else f"Whisper-Modelltest lieferte Gerät {actual_device!r} statt 'cuda'."

    @classmethod
    def gpu_available(cls) -> bool:
        return cls._cuda_device_issue() is None

    @classmethod
    def available_execution_modes(cls) -> list[str]:
        modes = ["auto", "cpu"]
        if cls.gpu_available():
            modes.append("cuda")
        return modes

    @classmethod
    def cuda_diagnostic_report(cls) -> str:
        lines = ["CUDA-Diagnose", f"Plattform: {sys.platform}", f"CTranslate2: {'installiert' if ctranslate2 is not None else 'nicht installiert'}"]
        if ctranslate2 is not None:
            try:
                count = ctranslate2.get_cuda_device_count()
            except Exception as exc:
                lines.append(f"CUDA-Geräteprüfung: fehlgeschlagen ({exc})")
            else:
                lines.append(f"Gefundene CUDA-Geräte: {count}")
        if sys.platform == "win32":
            entries = [e.strip() for e in os.environ.get("PATH", "").split(os.pathsep) if e.strip()]
            cuda_entries = [e for e in entries if any(token in e.lower() for token in ("cuda", "cudnn", "nvidia"))]
            if cuda_entries:
                lines.append("Relevante PATH-Einträge:")
                for entry in cuda_entries[:8]:
                    lines.append(f"  - {entry}")
                if len(cuda_entries) > 8:
                    lines.append(f"  - ... ({len(cuda_entries) - 8} weitere Einträge)")
            else:
                lines.append("Relevante PATH-Einträge: keine CUDA-/cuDNN-Pfade gefunden")
        else:
            lines.append("Relevante PATH-Einträge: nicht geprüft (kein Windows)")
        smoke = cls._cuda_model_smoke_test_issue()
        if smoke is None:
            lines += ["Whisper-Modelltest: erfolgreich (device='cuda')", "Status: CUDA ist für Whisper nutzbar.", "Empfehlung: Der Modus 'cuda' kann verwendet werden."]
        else:
            lines.append("Whisper-Modelltest: fehlgeschlagen")
            lines.append("Status: CUDA-Modelltest konnte nicht vollständig ausgeführt werden." if "lokale 'tiny'-Modell" in smoke or "lokales 'tiny'-Modell" in smoke else "Status: CUDA ist in dieser App nicht nutzbar.")
            lines.append(f"Details: {smoke}")
            lines.append("Empfehlung: Prüfe den echten Whisper-Modelltest in genau dem Prozess, der die App startet, oder verwende 'auto' bzw. 'cpu'.")
        return "\n".join(lines)

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16_000,
        model_size: str = "small",
        language: str | None = "de",
        execution_mode: str = "auto",
        speaker_diarization: bool = False,
        max_speakers: int = 2,
        on_progress: Callable[[str], None] | None = None,
    ) -> TranscriptionResult:
        if audio.size == 0:
            raise ValueError("Keine Audiodaten zum Transkribieren vorhanden.")
        if on_progress:
            on_progress("Whisper-Modell wird geladen...")
        resolved_device, resolved_compute_type = self._ensure_model(model_size, execution_mode, on_progress)
        actual_device = getattr(getattr(self._model, "model", None), "device", resolved_device)
        if on_progress:
            on_progress(f"Whisper meldet aktives Gerät: {actual_device}")
            on_progress(f"Transkription läuft auf {actual_device.upper()} ({resolved_compute_type})...")
        try:
            whisper_segments, info = self._model.transcribe(
                audio,
                language=None if language == "auto" else language,
                beam_size=5,
                vad_filter=True,
            )
            whisper_segments = list(whisper_segments)
        except Exception as exc:
            if actual_device == "cuda" and self._is_dll_load_error(exc):
                self._ensure_windows_cuda_runtime_paths()
                try:
                    whisper_segments, info = self._model.transcribe(
                        audio,
                        language=None if language == "auto" else language,
                        beam_size=5,
                        vad_filter=True,
                    )
                    whisper_segments = list(whisper_segments)
                except Exception as retry_exc:
                    raise RuntimeError(f"Whisper-Transkription fehlgeschlagen auf {actual_device}: {retry_exc}") from retry_exc
            else:
                raise RuntimeError(f"Whisper-Transkription fehlgeschlagen auf {actual_device}: {exc}") from exc
        if on_progress:
            on_progress(f"Whisper-Transkription abgeschlossen auf {actual_device}.")
        transcript_segments = self._collect_transcript_segments(whisper_segments)
        if speaker_diarization and transcript_segments:
            if on_progress:
                on_progress("Sprecher werden unterschieden...")
            transcript_segments = self._apply_speaker_diarization(audio, sample_rate, transcript_segments, max_speakers)
        full_text = self._compose_transcript_text(transcript_segments)
        return TranscriptionResult(full_text, info.language or (language or "auto"), len(audio) / sample_rate, transcript_segments)

    def _collect_transcript_segments(self, whisper_segments) -> list[TranscriptSegment]:
        out: list[TranscriptSegment] = []
        for segment in whisper_segments:
            text = segment.text.strip()
            if text:
                out.append(TranscriptSegment(float(segment.start or 0.0), float(segment.end or segment.start or 0.0), text))
        return out

    def _compose_transcript_text(self, segments: list[TranscriptSegment]) -> str:
        if not segments:
            return ""
        return self._format_speaker_text(segments) if any(s.speaker for s in segments) else " ".join(s.text for s in segments).strip()

    def _assign_speakers(
        self,
        audio: np.ndarray,
        sample_rate: int,
        segments: list[TranscriptSegment],
        max_speakers: int,
    ) -> list[TranscriptSegment]:
        return self._apply_speaker_diarization(audio, sample_rate, segments, max_speakers)

    def _apply_speaker_diarization(
        self,
        audio: np.ndarray,
        sample_rate: int,
        segments: list[TranscriptSegment],
        max_speakers: int,
    ) -> list[TranscriptSegment]:
        max_speakers = max(1, min(int(max_speakers), 8))
        speech_regions = self._detect_speech_regions(audio, sample_rate)
        embeddings: list[np.ndarray] = []
        valid_regions: list[SpeechRegion] = []
        for region in speech_regions:
            emb = self._segment_embedding(audio, sample_rate, region.start, region.end)
            if emb is not None:
                embeddings.append(emb)
                valid_regions.append(region)
        if not valid_regions:
            return [TranscriptSegment(s.start, s.end, s.text, "Sprecher 1") for s in segments]
        labels = self._cluster_speakers(np.vstack(embeddings), max_speakers)
        speaker_order: dict[int, int] = {}
        for region, label in zip(valid_regions, labels):
            region.speaker_label = int(label)
            speaker_order.setdefault(region.speaker_label, len(speaker_order) + 1)
        result: list[TranscriptSegment] = []
        for segment in segments:
            label = self._speaker_label_for_segment(segment, valid_regions)
            speaker_no = speaker_order.setdefault(label, len(speaker_order) + 1)
            result.append(TranscriptSegment(segment.start, segment.end, segment.text, f"Sprecher {speaker_no}"))
        return result

    def _detect_speech_regions(
        self,
        audio: np.ndarray,
        sample_rate: int,
        frame_duration_seconds: float = 0.03,
        hop_duration_seconds: float = 0.015,
        min_speech_duration: float = 0.35,
        min_silence_duration: float = 0.2,
    ) -> list[SpeechRegion]:
        mono = np.asarray(audio, dtype=np.float32)
        if mono.ndim > 1:
            mono = mono.mean(axis=1)
        if mono.size == 0:
            return []
        total_duration = mono.size / sample_rate
        frame_length = max(1, int(frame_duration_seconds * sample_rate))
        hop_length = max(1, int(hop_duration_seconds * sample_rate))
        if mono.size <= frame_length:
            return [SpeechRegion(0.0, total_duration)]
        rms_values: list[float] = []
        frame_starts: list[int] = []
        for start in range(0, mono.size - frame_length + 1, hop_length):
            frame = mono[start : start + frame_length]
            rms_values.append(float(np.sqrt(np.mean(frame**2))))
            frame_starts.append(start)
        if not rms_values:
            return [SpeechRegion(0.0, total_duration)]
        energy = np.asarray(rms_values, dtype=np.float32)
        if float(np.max(energy)) <= 1e-6:
            return [SpeechRegion(0.0, total_duration)]
        threshold = max(1e-4, float(np.percentile(energy, 90)) * 0.25, float(np.percentile(energy, 75)) * 0.55, float(np.median(energy)) * 4.0)
        speech_flags = energy > threshold
        if not np.any(speech_flags):
            return [SpeechRegion(0.0, total_duration)]
        raw: list[SpeechRegion] = []
        start_frame: int | None = None
        for idx, is_speech in enumerate(speech_flags):
            if is_speech and start_frame is None:
                start_frame = idx
            elif not is_speech and start_frame is not None:
                raw.append(SpeechRegion(frame_starts[start_frame] / sample_rate, min(total_duration, (frame_starts[idx] + frame_length) / sample_rate)))
                start_frame = None
        if start_frame is not None:
            raw.append(SpeechRegion(frame_starts[start_frame] / sample_rate, total_duration))
        merged: list[SpeechRegion] = []
        for region in raw:
            if merged and region.start - merged[-1].end <= min_silence_duration:
                merged[-1].end = max(merged[-1].end, region.end)
            else:
                merged.append(region)
        filtered = [region for region in merged if (region.end - region.start) >= min_speech_duration]
        return filtered or [SpeechRegion(0.0, total_duration)]

    def _speaker_label_for_segment(self, segment: TranscriptSegment, regions: list[SpeechRegion]) -> int:
        best_label: int | None = None
        best_overlap = float("-inf")
        nearest_label = 1
        nearest_distance = float("inf")
        midpoint = (segment.start + segment.end) * 0.5
        for region in regions:
            label = region.speaker_label or 1
            overlap = min(segment.end, region.end) - max(segment.start, region.start)
            if overlap > best_overlap:
                best_overlap = overlap
                if overlap > 0:
                    best_label = label
            region_midpoint = (region.start + region.end) * 0.5
            distance = min(abs(segment.start - region.end), abs(segment.end - region.start), abs(midpoint - region_midpoint))
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_label = label
        return best_label if best_label is not None else nearest_label

    def _segment_embedding(self, audio: np.ndarray, sample_rate: int, start_seconds: float, end_seconds: float) -> np.ndarray | None:
        start_index = max(0, int(start_seconds * sample_rate))
        end_index = min(len(audio), int(max(end_seconds, start_seconds + 0.25) * sample_rate))
        if end_index - start_index < int(0.2 * sample_rate):
            return None
        chunk = np.asarray(audio[start_index:end_index], dtype=np.float32)
        if chunk.ndim > 1:
            chunk = chunk.mean(axis=1)
        if chunk.size < 128:
            return None
        peak = float(np.max(np.abs(chunk)))
        if peak > 1e-6:
            chunk = chunk / peak
        target_min = int(0.6 * sample_rate)
        if chunk.size < target_min:
            chunk = np.pad(chunk, (0, target_min - chunk.size))
        target_max = int(2.5 * sample_rate)
        if chunk.size > target_max:
            center = chunk.size // 2
            half = target_max // 2
            chunk = chunk[max(0, center - half) : min(chunk.size, center + half)]
        nperseg = min(400, chunk.size)
        if nperseg < 64:
            return None
        noverlap = min(int(nperseg * 0.6), nperseg - 1)
        freqs, _, spec = spectrogram(chunk, fs=sample_rate, window="hann", nperseg=nperseg, noverlap=noverlap, scaling="spectrum", mode="magnitude")
        if spec.size == 0:
            return None
        power = spec.astype(np.float32) ** 2 + 1e-8
        band_count = min(20, power.shape[0])
        if band_count < 4:
            return None
        edges = np.linspace(0, power.shape[0], num=band_count + 1, dtype=int)
        bands = [power[s:max(s + 1, e)].mean(axis=0) for s, e in zip(edges[:-1], edges[1:])]
        log_bands = np.log1p(np.vstack(bands))
        mfcc_like = dct(log_bands, axis=0, norm="ortho")[:8]
        centroid = (freqs[:, None] * power).sum(axis=0) / (power.sum(axis=0) + 1e-8)
        cumulative_energy = np.cumsum(power, axis=0)
        rolloff_indices = (cumulative_energy >= 0.85 * cumulative_energy[-1:]).argmax(axis=0)
        rolloff = freqs[rolloff_indices]
        zcr = float(np.mean(chunk[:-1] * chunk[1:] < 0))
        rms = float(np.sqrt(np.mean(chunk**2)))
        emb = np.concatenate([
            mfcc_like.mean(axis=1),
            mfcc_like.std(axis=1),
            np.array([
                float(np.mean(centroid) / sample_rate),
                float(np.std(centroid) / sample_rate),
                float(np.mean(rolloff) / sample_rate),
                float(np.std(rolloff) / sample_rate),
                zcr,
                rms,
            ], dtype=np.float32),
        ]).astype(np.float32)
        norm = float(np.linalg.norm(emb))
        return emb / norm if norm > 1e-6 else emb

    def _cluster_speakers(self, embeddings: np.ndarray, max_speakers: int) -> np.ndarray:
        n = len(embeddings)
        if n <= 1 or max_speakers <= 1:
            return np.ones(n, dtype=int)
        normalized = embeddings.astype(np.float32)
        normalized = normalized / np.clip(np.linalg.norm(normalized, axis=1, keepdims=True), 1e-8, None)
        pairwise = pdist(normalized, metric="cosine")
        if pairwise.size == 0 or np.allclose(pairwise, 0.0):
            return np.ones(n, dtype=int)
        if n == 2:
            return np.array([1, 2], dtype=int) if pairwise[0] >= 0.18 else np.ones(2, dtype=int)
        hierarchy = linkage(pairwise, method="average")
        distance_matrix = squareform(pairwise)
        best_labels = np.ones(n, dtype=int)
        best_score = float("-inf")
        for cluster_count in range(1, min(max_speakers, n) + 1):
            labels = fcluster(hierarchy, cluster_count, criterion="maxclust")
            score = self._cluster_quality(distance_matrix, normalized, labels)
            if score > best_score:
                best_score = score
                best_labels = labels.astype(int)
        return best_labels

    def _cluster_quality(self, distance_matrix: np.ndarray, embeddings: np.ndarray, labels: np.ndarray) -> float:
        unique_labels = sorted(set(int(label) for label in labels))
        if len(unique_labels) == 1:
            upper = distance_matrix[np.triu_indices_from(distance_matrix, k=1)]
            return 0.02 - float(upper.mean()) if upper.size else 0.0
        intra_distances: list[float] = []
        centroids: list[np.ndarray] = []
        singleton_count = 0
        for label in unique_labels:
            idx = np.where(labels == label)[0]
            if len(idx) == 1:
                singleton_count += 1
            else:
                upper = distance_matrix[np.ix_(idx, idx)][np.triu_indices(len(idx), k=1)]
                if upper.size:
                    intra_distances.append(float(upper.mean()))
            centroid = embeddings[idx].mean(axis=0)
            norm = float(np.linalg.norm(centroid))
            centroids.append(centroid / norm if norm > 1e-6 else centroid)
        intra = float(np.mean(intra_distances)) if intra_distances else 0.0
        inter = float(np.mean(pdist(np.vstack(centroids), metric="cosine"))) if len(centroids) > 1 else 0.0
        return inter - intra - 0.035 * (len(unique_labels) - 1) - 0.03 * singleton_count

    def _merge_adjacent_segments(self, segments: list[TranscriptSegment], max_gap_seconds: float = 1.0) -> list[TranscriptSegment]:
        if not segments:
            return []
        merged = [TranscriptSegment(segments[0].start, segments[0].end, segments[0].text, segments[0].speaker)]
        for segment in segments[1:]:
            previous = merged[-1]
            if previous.speaker == segment.speaker and segment.start - previous.end <= max_gap_seconds:
                previous.end = max(previous.end, segment.end)
                previous.text = f"{previous.text} {segment.text}".strip()
            else:
                merged.append(TranscriptSegment(segment.start, segment.end, segment.text, segment.speaker))
        return merged

    def _format_speaker_text(self, segments: list[TranscriptSegment]) -> str:
        return "\n\n".join(f"{segment.speaker or 'Sprecher ?'} [{self._format_timestamp(segment.start)} - {self._format_timestamp(segment.end)}]: {segment.text}" for segment in segments).strip()

    def _format_timestamp(self, seconds: float) -> str:
        total_seconds = max(0, int(round(seconds)))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"

    def _ensure_model(self, model_size: str, execution_mode: str = "auto", on_progress: Callable[[str], None] | None = None) -> tuple[str, str]:
        self._ensure_windows_cuda_runtime_paths()
        requested_device, requested_compute_type = self._resolve_execution_mode(execution_mode)
        requested_config = (model_size, requested_device, requested_compute_type)
        if self._model is not None and self._loaded_config == requested_config:
            return requested_device, requested_compute_type
        if on_progress:
            on_progress(f"Modell '{model_size}' wird auf {requested_device.upper()} geladen...")
        try:
            self._model = WhisperModel(model_size, device=requested_device, compute_type=requested_compute_type)
        except Exception as exc:
            if requested_device == "cuda" and self._is_dll_load_error(exc):
                self._ensure_windows_cuda_runtime_paths()
                try:
                    self._model = WhisperModel(model_size, device=requested_device, compute_type=requested_compute_type)
                except Exception as retry_exc:
                    raise RuntimeError(f"Whisper konnte nicht auf {requested_device.upper()} geladen werden: {retry_exc}") from retry_exc
            else:
                raise RuntimeError(f"Whisper konnte nicht auf {requested_device.upper()} geladen werden: {exc}") from exc
        self._loaded_config = requested_config
        return requested_device, requested_compute_type

    def _resolve_execution_mode(self, execution_mode: str) -> tuple[str, str]:
        mode = execution_mode.lower().strip()
        if mode not in self.EXECUTION_MODES:
            raise ValueError(f"Unbekannter Rechenmodus: {execution_mode}")
        if mode == "cpu":
            return "cpu", "int8"
        if mode == "cuda":
            issue = self._cuda_device_issue()
            if issue is not None:
                raise RuntimeError(f"CUDA-Modus ist nicht verfügbar: {issue}")
            return "cuda", "float16"
        return ("cuda", "float16") if self.gpu_available() else ("cpu", "int8")


__all__ = ["SpeechRegion", "TranscriptSegment", "TranscriptionResult", "WhisperTranscriber"]

