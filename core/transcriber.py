"""Whisper-Transkription mit optionaler Sprecher-Unterscheidung."""

from __future__ import annotations

from dataclasses import dataclass, field
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

    def __init__(self) -> None:
        self._model: WhisperModel | None = None
        self._loaded_config: tuple[str, str, str] | None = None

    @classmethod
    def gpu_available(cls) -> bool:
        if ctranslate2 is None:
            return False
        try:
            return ctranslate2.get_cuda_device_count() > 0
        except Exception:
            return False

    @classmethod
    def available_execution_modes(cls) -> list[str]:
        modes = ["auto", "cpu"]
        if cls.gpu_available():
            modes.append("cuda")
        return modes

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

        resolved_device, resolved_compute_type = self._ensure_model(
            model_size,
            execution_mode,
            on_progress,
        )

        if on_progress:
            on_progress(
                f"Transkription läuft ({resolved_device.upper()}, {resolved_compute_type})..."
            )

        segments, info = self._model.transcribe(
            audio,
            language=None if language == "auto" else language,
            beam_size=5,
            vad_filter=True,
        )

        transcript_segments: list[TranscriptSegment] = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            transcript_segments.append(
                TranscriptSegment(
                    start=float(segment.start or 0.0),
                    end=float(segment.end or segment.start or 0.0),
                    text=text,
                )
            )

        if speaker_diarization and transcript_segments:
            if on_progress:
                on_progress("Sprecher werden unterschieden...")
            transcript_segments = self._assign_speakers(
                audio=audio,
                sample_rate=sample_rate,
                segments=transcript_segments,
                max_speakers=max_speakers,
            )
            transcript_segments = self._merge_adjacent_segments(transcript_segments)
            full_text = self._format_speaker_text(transcript_segments)
        else:
            full_text = " ".join(segment.text for segment in transcript_segments).strip()

        duration = len(audio) / sample_rate

        return TranscriptionResult(
            text=full_text,
            language=info.language or (language or "auto"),
            duration=duration,
            segments=transcript_segments,
        )

    def _assign_speakers(
        self,
        audio: np.ndarray,
        sample_rate: int,
        segments: list[TranscriptSegment],
        max_speakers: int,
    ) -> list[TranscriptSegment]:
        max_speakers = max(1, min(int(max_speakers), 8))
        embeddings: list[np.ndarray] = []
        embedding_indices: list[int] = []

        for index, segment in enumerate(segments):
            embedding = self._segment_embedding(audio, sample_rate, segment.start, segment.end)
            if embedding is None:
                continue
            embeddings.append(embedding)
            embedding_indices.append(index)

        if not embeddings:
            return [
                TranscriptSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    speaker="Sprecher 1",
                )
                for segment in segments
            ]

        labels = self._cluster_speakers(np.vstack(embeddings), max_speakers=max_speakers)
        cluster_by_index = {segment_index: int(label) for segment_index, label in zip(embedding_indices, labels)}

        if cluster_by_index:
            ordered_indices = sorted(cluster_by_index)
            for index in range(len(segments)):
                if index in cluster_by_index:
                    continue
                nearest_index = min(ordered_indices, key=lambda candidate: abs(candidate - index))
                cluster_by_index[index] = cluster_by_index[nearest_index]

        speaker_order: dict[int, int] = {}
        labeled_segments: list[TranscriptSegment] = []
        for index, segment in enumerate(segments):
            cluster_label = cluster_by_index.get(index, 1)
            if cluster_label not in speaker_order:
                speaker_order[cluster_label] = len(speaker_order) + 1
            speaker_number = speaker_order[cluster_label]
            labeled_segments.append(
                TranscriptSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    speaker=f"Sprecher {speaker_number}",
                )
            )

        return labeled_segments

    def _segment_embedding(
        self,
        audio: np.ndarray,
        sample_rate: int,
        start_seconds: float,
        end_seconds: float,
    ) -> np.ndarray | None:
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

        target_min_length = int(0.6 * sample_rate)
        if chunk.size < target_min_length:
            chunk = np.pad(chunk, (0, target_min_length - chunk.size))

        nperseg = min(400, chunk.size)
        if nperseg < 64:
            return None
        noverlap = min(int(nperseg * 0.6), nperseg - 1)

        frequencies, _, spectrum = spectrogram(
            chunk,
            fs=sample_rate,
            window="hann",
            nperseg=nperseg,
            noverlap=noverlap,
            scaling="spectrum",
            mode="magnitude",
        )
        if spectrum.size == 0:
            return None

        power = spectrum.astype(np.float32) ** 2 + 1e-8
        band_count = min(20, power.shape[0])
        if band_count < 4:
            return None

        band_edges = np.linspace(0, power.shape[0], num=band_count + 1, dtype=int)
        band_energies: list[np.ndarray] = []
        for start_bin, end_bin in zip(band_edges[:-1], band_edges[1:]):
            effective_end = max(start_bin + 1, end_bin)
            band_energies.append(power[start_bin:effective_end].mean(axis=0))
        bands = np.vstack(band_energies)
        log_bands = np.log(bands)

        mfcc_like = dct(log_bands, axis=0, norm="ortho")[:8]
        spectral_centroid = (frequencies[:, None] * power).sum(axis=0) / (power.sum(axis=0) + 1e-8)
        cumulative_energy = np.cumsum(power, axis=0)
        rolloff_indices = (cumulative_energy >= 0.85 * cumulative_energy[-1:]).argmax(axis=0)
        spectral_rolloff = frequencies[rolloff_indices]
        zero_crossing_rate = float(np.mean(chunk[:-1] * chunk[1:] < 0))
        rms = float(np.sqrt(np.mean(chunk**2)))

        embedding = np.concatenate(
            [
                mfcc_like.mean(axis=1),
                mfcc_like.std(axis=1),
                np.array(
                    [
                        float(np.mean(spectral_centroid) / sample_rate),
                        float(np.std(spectral_centroid) / sample_rate),
                        float(np.mean(spectral_rolloff) / sample_rate),
                        float(np.std(spectral_rolloff) / sample_rate),
                        zero_crossing_rate,
                        rms,
                    ],
                    dtype=np.float32,
                ),
            ]
        ).astype(np.float32)

        norm = float(np.linalg.norm(embedding))
        if norm > 1e-6:
            embedding = embedding / norm
        return embedding

    def _cluster_speakers(self, embeddings: np.ndarray, max_speakers: int) -> np.ndarray:
        segment_count = len(embeddings)
        if segment_count <= 1 or max_speakers <= 1:
            return np.ones(segment_count, dtype=int)

        normalized = embeddings.astype(np.float32)
        row_norms = np.linalg.norm(normalized, axis=1, keepdims=True)
        normalized = normalized / np.clip(row_norms, 1e-8, None)

        pairwise_distances = pdist(normalized, metric="cosine")
        if pairwise_distances.size == 0 or np.allclose(pairwise_distances, 0.0):
            return np.ones(segment_count, dtype=int)

        if segment_count == 2:
            return np.array([1, 2], dtype=int) if pairwise_distances[0] >= 0.18 else np.ones(2, dtype=int)

        hierarchy = linkage(pairwise_distances, method="average")
        distance_matrix = squareform(pairwise_distances)

        best_labels = np.ones(segment_count, dtype=int)
        best_score = float("-inf")
        for cluster_count in range(1, min(max_speakers, segment_count) + 1):
            labels = fcluster(hierarchy, cluster_count, criterion="maxclust")
            score = self._cluster_quality(distance_matrix, normalized, labels)
            if score > best_score:
                best_score = score
                best_labels = labels.astype(int)

        return best_labels

    def _cluster_quality(
        self,
        distance_matrix: np.ndarray,
        embeddings: np.ndarray,
        labels: np.ndarray,
    ) -> float:
        unique_labels = sorted(set(int(label) for label in labels))
        if len(unique_labels) == 1:
            upper = distance_matrix[np.triu_indices_from(distance_matrix, k=1)]
            return 0.02 - float(upper.mean()) if upper.size else 0.0

        intra_distances: list[float] = []
        centroids: list[np.ndarray] = []
        singleton_count = 0

        for label in unique_labels:
            member_indices = np.where(labels == label)[0]
            if len(member_indices) == 1:
                singleton_count += 1
            else:
                cluster_distances = distance_matrix[np.ix_(member_indices, member_indices)]
                upper = cluster_distances[np.triu_indices_from(cluster_distances, k=1)]
                if upper.size:
                    intra_distances.append(float(upper.mean()))

            centroid = embeddings[member_indices].mean(axis=0)
            centroid_norm = float(np.linalg.norm(centroid))
            if centroid_norm > 1e-6:
                centroid = centroid / centroid_norm
            centroids.append(centroid)

        intra = float(np.mean(intra_distances)) if intra_distances else 0.0
        inter = float(np.mean(pdist(np.vstack(centroids), metric="cosine"))) if len(centroids) > 1 else 0.0
        cluster_penalty = 0.035 * (len(unique_labels) - 1)
        singleton_penalty = 0.03 * singleton_count
        return inter - intra - cluster_penalty - singleton_penalty

    def _merge_adjacent_segments(
        self,
        segments: list[TranscriptSegment],
        max_gap_seconds: float = 1.0,
    ) -> list[TranscriptSegment]:
        if not segments:
            return []

        merged = [
            TranscriptSegment(
                start=segments[0].start,
                end=segments[0].end,
                text=segments[0].text,
                speaker=segments[0].speaker,
            )
        ]

        for segment in segments[1:]:
            previous = merged[-1]
            if (
                previous.speaker == segment.speaker
                and segment.start - previous.end <= max_gap_seconds
            ):
                previous.end = max(previous.end, segment.end)
                previous.text = f"{previous.text} {segment.text}".strip()
            else:
                merged.append(
                    TranscriptSegment(
                        start=segment.start,
                        end=segment.end,
                        text=segment.text,
                        speaker=segment.speaker,
                    )
                )

        return merged

    def _format_speaker_text(self, segments: list[TranscriptSegment]) -> str:
        lines = []
        for segment in segments:
            speaker = segment.speaker or "Sprecher ?"
            start = self._format_timestamp(segment.start)
            end = self._format_timestamp(segment.end)
            lines.append(f"{speaker} [{start} - {end}]: {segment.text}")
        return "\n\n".join(lines).strip()


    def _format_timestamp(self, seconds: float) -> str:
        total_seconds = max(0, int(round(seconds)))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _ensure_model(

        self,
        model_size: str,
        execution_mode: str = "auto",
        on_progress: Callable[[str], None] | None = None,
    ) -> tuple[str, str]:
        requested_device, requested_compute_type = self._resolve_execution_mode(execution_mode)
        requested_config = (model_size, requested_device, requested_compute_type)

        if self._model is not None and self._loaded_config == requested_config:
            return requested_device, requested_compute_type

        if on_progress:
            on_progress(
                f"Modell '{model_size}' wird auf {requested_device.upper()} geladen..."
            )

        try:
            self._model = WhisperModel(
                model_size,
                device=requested_device,
                compute_type=requested_compute_type,
            )
            self._loaded_config = requested_config
            return requested_device, requested_compute_type
        except Exception as exc:
            if execution_mode != "auto" or requested_device != "cuda":
                raise RuntimeError(
                    f"Whisper konnte nicht auf {requested_device.upper()} geladen werden: {exc}"
                ) from exc

            if on_progress:
                on_progress("CUDA nicht verfügbar/fehlgeschlagen, wechsle auf CPU...")

            fallback_device, fallback_compute_type = "cpu", "int8"
            self._model = WhisperModel(
                model_size,
                device=fallback_device,
                compute_type=fallback_compute_type,
            )
            self._loaded_config = (model_size, fallback_device, fallback_compute_type)
            return fallback_device, fallback_compute_type

    def _resolve_execution_mode(self, execution_mode: str) -> tuple[str, str]:
        mode = execution_mode.lower().strip()
        if mode not in self.EXECUTION_MODES:
            raise ValueError(f"Unbekannter Rechenmodus: {execution_mode}")

        if mode == "cpu":
            return "cpu", "int8"

        if mode == "cuda":
            if not self.gpu_available():
                raise RuntimeError("Es wurde keine CUDA-fähige GPU für Whisper gefunden.")
            return "cuda", "float16"

        if self.gpu_available():
            return "cuda", "float16"
        return "cpu", "int8"


__all__ = [
    "TranscriptSegment",
    "TranscriptionResult",
    "WhisperTranscriber",
]

