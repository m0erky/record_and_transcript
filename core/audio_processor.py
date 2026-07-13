"""Audio-Verbesserung: Normalisierung, Filter und Rauschreduktion."""

from __future__ import annotations

from dataclasses import dataclass, field

import noisereduce as nr
import numpy as np
from scipy.signal import butter, sosfilt


@dataclass
class EnhancementOptions:
    normalize: bool = True
    high_pass: bool = True
    noise_reduce: bool = True
    target_peak: float = 0.9
    high_pass_cutoff_hz: float = 80.0
    noise_reduce_strength: float = 0.6


@dataclass
class EnhancementResult:
    audio: np.ndarray
    applied_steps: list[str] = field(default_factory=list)


class AudioProcessor:
    def __init__(self, sample_rate: int = 16_000) -> None:
        self.sample_rate = sample_rate

    def enhance(
        self,
        audio: np.ndarray,
        options: EnhancementOptions | None = None,
    ) -> EnhancementResult:
        if audio.size == 0:
            raise ValueError("Keine Audiodaten zum Verbessern vorhanden.")

        opts = options or EnhancementOptions()
        processed = audio.astype(np.float32).copy()
        steps: list[str] = []

        if opts.high_pass:
            processed = self._high_pass_filter(processed, opts.high_pass_cutoff_hz)
            steps.append(f"Hochpassfilter ({int(opts.high_pass_cutoff_hz)} Hz)")

        if opts.noise_reduce:
            processed = self._reduce_noise(processed, opts.noise_reduce_strength)
            steps.append("Rauschreduktion")

        if opts.normalize:
            processed = self._normalize(processed, opts.target_peak)
            steps.append("Lautstärke-Normalisierung")

        return EnhancementResult(audio=processed, applied_steps=steps)

    def _high_pass_filter(self, audio: np.ndarray, cutoff_hz: float) -> np.ndarray:
        nyquist = 0.5 * self.sample_rate
        normalized_cutoff = min(cutoff_hz / nyquist, 0.99)
        sos = butter(4, normalized_cutoff, btype="highpass", output="sos")
        return sosfilt(sos, audio).astype(np.float32)

    def _reduce_noise(self, audio: np.ndarray, strength: float) -> np.ndarray:
        clamped_strength = float(np.clip(strength, 0.0, 1.0))
        return nr.reduce_noise(
            y=audio,
            sr=self.sample_rate,
            prop_decrease=clamped_strength,
            stationary=True,
        ).astype(np.float32)

    def _normalize(self, audio: np.ndarray, target_peak: float) -> np.ndarray:
        peak = float(np.max(np.abs(audio)))
        if peak < 1e-6:
            return audio
        scale = target_peak / peak
        normalized = audio * scale
        return np.clip(normalized, -1.0, 1.0).astype(np.float32)
