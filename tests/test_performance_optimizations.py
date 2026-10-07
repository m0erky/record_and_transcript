from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.waveform import WaveformCanvas
from core.audio_player import AudioPlayer


class AudioPlayerThrottlingTests(unittest.TestCase):
    def test_position_notifications_are_throttled_and_force_bypasses(self) -> None:
        player = AudioPlayer(sample_rate=10)
        player._audio = np.ones(100, dtype=np.float32)

        events: list[tuple[float, float]] = []
        player.set_callbacks(on_position_change=lambda pos, dur: events.append((pos, dur)))
        player._last_position_notify_monotonic = -1.0

        with patch("core.audio_player.time.monotonic", side_effect=[1.0, 1.02, 1.10, 1.11]):
            player._notify_position()
            player._notify_position()
            player._notify_position()
            player._notify_position(force=True)

        self.assertEqual(len(events), 3)
        self.assertAlmostEqual(events[0][1], 10.0, places=5)


class WaveformEnvelopeTests(unittest.TestCase):
    def test_compute_base_envelope_uses_chunk_max_abs(self) -> None:
        audio = np.array([0.1, -0.8, 0.3, -0.4, 0.9, -0.2, 0.5, -0.7], dtype=np.float32)

        envelope = WaveformCanvas._compute_base_envelope(audio, target_points=4)

        expected = np.array([0.8, 0.4, 0.9, 0.7], dtype=np.float32)
        np.testing.assert_allclose(envelope, expected)

    def test_resample_envelope_handles_single_point(self) -> None:
        envelope = np.array([0.42], dtype=np.float32)

        resampled = WaveformCanvas._resample_envelope(envelope, target_points=5)

        np.testing.assert_allclose(resampled, np.full(5, 0.42, dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
