from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_ensure_model_raises_when_cuda_model_load_fails(self) -> None:
        def fake_whisper_model(*_args, **kwargs):
            if kwargs.get("device") == "cuda":
                raise RuntimeError("cuda load failed")
            raise AssertionError("CPU fallback must not be attempted")

        with patch("core.transcriber.WhisperModel", side_effect=fake_whisper_model):
            with self.assertRaises(RuntimeError) as ctx:
                self.transcriber._ensure_model("tiny", "cuda")

        self.assertIn("Whisper konnte nicht auf CUDA geladen werden", str(ctx.exception))

    def test_transcribe_logs_actual_cuda_device_when_cuda_transcription_succeeds(self) -> None:
        fake_ctranslate2 = type(
            "FakeCTranslate2",
            (),
            {"get_cuda_device_count": staticmethod(lambda: 1)},
        )

        class FakeInfo:
            language = "de"

        class FakeCudaModel:
            def __init__(self) -> None:
                self.model = type("InnerModel", (), {"device": "cuda"})()

            def transcribe(self, *_args, **_kwargs):
                return iter([type("Seg", (), {"text": "Hallo", "start": 0.0, "end": 1.0})()]), FakeInfo()

        audio = np.ones(16000, dtype=np.float32)
        progress_messages: list[str] = []

        with patch("core.transcriber.ctranslate2", fake_ctranslate2), patch(
            "core.transcriber.WhisperModel",
            side_effect=lambda *args, **kwargs: FakeCudaModel(),
        ):
            result = self.transcriber.transcribe(
                audio=audio,
                execution_mode="cuda",
                on_progress=progress_messages.append,
            )

        self.assertEqual(result.text, "Hallo")
        self.assertEqual(self.transcriber._model.model.device, "cuda")
        self.assertTrue(any("Whisper meldet aktives Gerät: cuda" in msg for msg in progress_messages))
        self.assertTrue(any("Transkription läuft auf CUDA" in msg for msg in progress_messages))
        self.assertTrue(any("abgeschlossen auf cuda" in msg.lower() for msg in progress_messages))

    def test_transcribe_raises_when_cuda_transcription_fails(self) -> None:
        fake_ctranslate2 = type(
            "FakeCTranslate2",
            (),
            {"get_cuda_device_count": staticmethod(lambda: 1)},
        )

        class FakeCudaModel:
            def __init__(self) -> None:
                self.model = type("InnerModel", (), {"device": "cuda"})()

            def transcribe(self, *_args, **_kwargs):
                raise RuntimeError("CUDA inference failed")

        audio = np.ones(16000, dtype=np.float32)

        with patch("core.transcriber.ctranslate2", fake_ctranslate2), patch(
            "core.transcriber.WhisperModel",
            side_effect=lambda *args, **kwargs: FakeCudaModel(),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                self.transcriber.transcribe(audio=audio, execution_mode="cuda")

        self.assertIn("Whisper-Transkription fehlgeschlagen auf cuda", str(ctx.exception))

    def test_available_execution_modes_includes_cuda_when_cuda_device_is_detected(self) -> None:
        fake_ctranslate2 = type(
            "FakeCTranslate2",
            (),
            {"get_cuda_device_count": staticmethod(lambda: 1)},
        )

        with patch("core.transcriber.ctranslate2", fake_ctranslate2):
            modes = WhisperTranscriber.available_execution_modes()

        self.assertEqual(modes, ["auto", "cpu", "cuda"])

    def test_cuda_diagnostic_report_uses_whisper_model_smoke_test(self) -> None:
        fake_ctranslate2 = type(
            "FakeCTranslate2",
            (),
            {"get_cuda_device_count": staticmethod(lambda: 1)},
        )

        class FakeModel:
            def __init__(self) -> None:
                self.model = type("InnerModel", (), {"device": "cuda"})()

        with patch("core.transcriber.ctranslate2", fake_ctranslate2), patch(
            "core.transcriber.WhisperModel",
            side_effect=lambda *args, **kwargs: FakeModel(),
        ), patch("core.transcriber.sys.platform", "win32"), patch.dict(
            "core.transcriber.os.environ",
            {"PATH": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin"},
            clear=False,
        ):
            report = WhisperTranscriber.cuda_diagnostic_report()

        self.assertIn("CUDA-Diagnose", report)
        self.assertIn("Gefundene CUDA-Geräte: 1", report)
        self.assertIn("Whisper-Modelltest", report)
        self.assertIn("CUDA ist für Whisper nutzbar", report)
        self.assertNotIn("nicht ladbar", report)
        self.assertIn(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin", report)


if __name__ == "__main__":
    unittest.main()
