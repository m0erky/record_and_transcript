from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.transcriber import SpeechRegion, TranscriptSegment, WhisperTranscriber


class WhisperTranscriberTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transcriber = WhisperTranscriber()

    def test_detect_speech_regions_splits_separated_bursts(self) -> None:
        sample_rate = 1000
        audio = np.zeros(sample_rate * 5, dtype=np.float32)
        audio[500:1200] = 0.5
        audio[2500:3300] = 0.5

        regions = self.transcriber._detect_speech_regions(
            audio,
            sample_rate,
            frame_duration_seconds=0.05,
            hop_duration_seconds=0.025,
            min_speech_duration=0.1,
            min_silence_duration=0.1,
        )

        self.assertGreaterEqual(len(regions), 2)
        self.assertLess(regions[0].end, regions[1].start)
        self.assertLessEqual(regions[0].start, 0.6)
        self.assertGreaterEqual(regions[1].start, 2.3)

    def test_assign_speakers_maps_segments_to_closest_region(self) -> None:
        audio = np.zeros(4000, dtype=np.float32)
        segments = [
            TranscriptSegment(0.0, 0.9, "Hallo"),
            TranscriptSegment(1.0, 1.9, "Welt"),
            TranscriptSegment(2.8, 3.4, "Noch einmal"),
        ]
        regions = [
            SpeechRegion(0.0, 1.0),
            SpeechRegion(1.0, 2.0),
        ]
        for index, region in enumerate(regions):
            region.speaker_label = index + 2

        self.transcriber._detect_speech_regions = lambda _audio, _sr: regions  # type: ignore[method-assign]
        self.transcriber._segment_embedding = lambda _audio, _sr, _start, _end: np.array([1.0, 0.0], dtype=np.float32)  # type: ignore[method-assign]
        self.transcriber._cluster_speakers = lambda embeddings, max_speakers: np.array([2, 1], dtype=int)  # type: ignore[method-assign]

        labeled = self.transcriber._assign_speakers(
            audio=audio,
            sample_rate=1000,
            segments=segments,
            max_speakers=2,
        )

        self.assertEqual([segment.speaker for segment in labeled], ["Sprecher 1", "Sprecher 2", "Sprecher 2"])

    def test_merge_adjacent_segments_combines_same_speaker(self) -> None:
        segments = [
            TranscriptSegment(0.0, 1.0, "Hallo", "Sprecher 1"),
            TranscriptSegment(1.2, 2.0, "Welt", "Sprecher 1"),
            TranscriptSegment(2.5, 3.0, "Anderer", "Sprecher 2"),
        ]

        merged = self.transcriber._merge_adjacent_segments(segments, max_gap_seconds=0.5)

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].text, "Hallo Welt")
        self.assertEqual(merged[0].speaker, "Sprecher 1")
        self.assertEqual(merged[1].speaker, "Sprecher 2")


if __name__ == "__main__":
    unittest.main()
