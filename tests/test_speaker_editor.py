from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.backends.base import TranscriptSegment
from app.speaker_editor import (
    compose_transcript_text_from_segments,
    merge_speakers_in_segments,
    rename_speaker_in_segments,
    speaker_names_from_segments,
)


class SpeakerEditorTests(unittest.TestCase):
    def test_speaker_names_follow_first_occurrence_order(self) -> None:
        segments = [
            TranscriptSegment(0.0, 1.0, "Hallo", "Sprecher 2"),
            TranscriptSegment(1.0, 2.0, "Welt", "Sprecher 1"),
            TranscriptSegment(2.0, 3.0, "Nochmal", "Sprecher 2"),
        ]

        self.assertEqual(speaker_names_from_segments(segments), ["Sprecher 2", "Sprecher 1"])

    def test_rename_speaker_changes_only_matching_segments(self) -> None:
        segments = [
            TranscriptSegment(0.0, 1.0, "A", "Sprecher 1"),
            TranscriptSegment(1.0, 2.0, "B", "Sprecher 2"),
        ]

        renamed = rename_speaker_in_segments(
            segments,
            old_name="Sprecher 1",
            new_name="Interviewer",
        )

        self.assertEqual([segment.speaker for segment in renamed], ["Interviewer", "Sprecher 2"])

    def test_merge_speakers_relabels_source_to_target(self) -> None:
        segments = [
            TranscriptSegment(0.0, 1.0, "A", "Sprecher 1"),
            TranscriptSegment(1.0, 2.0, "B", "Sprecher 2"),
            TranscriptSegment(2.0, 3.0, "C", "Sprecher 1"),
        ]

        merged = merge_speakers_in_segments(
            segments,
            source_name="Sprecher 2",
            target_name="Sprecher 1",
        )

        self.assertEqual([segment.speaker for segment in merged], ["Sprecher 1", "Sprecher 1", "Sprecher 1"])

    def test_rename_preserves_speaker_confidence(self) -> None:
        segments = [TranscriptSegment(0.0, 1.0, "A", "Sprecher 1", 0.78)]

        renamed = rename_speaker_in_segments(segments, old_name="Sprecher 1", new_name="Host")

        self.assertEqual(renamed[0].speaker, "Host")
        self.assertAlmostEqual(renamed[0].speaker_confidence or 0.0, 0.78, places=5)

    def test_merge_preserves_speaker_confidence(self) -> None:
        segments = [TranscriptSegment(0.0, 1.0, "A", "Sprecher 2", 0.64)]

        merged = merge_speakers_in_segments(segments, source_name="Sprecher 2", target_name="Sprecher 1")

        self.assertEqual(merged[0].speaker, "Sprecher 1")
        self.assertAlmostEqual(merged[0].speaker_confidence or 0.0, 0.64, places=5)

    def test_compose_transcript_text_with_speakers_includes_labels_and_timestamps(self) -> None:
        segments = [
            TranscriptSegment(0.0, 1.4, "Hallo", "Interviewer"),
            TranscriptSegment(65.0, 68.0, "Antwort", "Gast"),
        ]

        text = compose_transcript_text_from_segments(segments)

        self.assertIn("Interviewer [00:00 - 00:01]: Hallo", text)
        self.assertIn("Gast [01:05 - 01:08]: Antwort", text)


if __name__ == "__main__":
    unittest.main()
