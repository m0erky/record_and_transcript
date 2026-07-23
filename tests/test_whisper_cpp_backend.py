from __future__ import annotations

import os
import tempfile
import shutil
import unittest
from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import MagicMock, patch

import numpy as np

from app.backends.base import BackendConfigurationError, TranscriptSegment
from app.backends.whisper_cpp_backend import WhisperCppBackend


class WhisperCppBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model_fd, self.model_path = tempfile.mkstemp(suffix=".bin")
        os.close(self.model_fd)
        self.binary_fd, self.binary_path = tempfile.mkstemp(suffix=".exe")
        os.close(self.binary_fd)

    def tearDown(self) -> None:
        Path(self.model_path).unlink(missing_ok=True)
        Path(self.binary_path).unlink(missing_ok=True)

    def test_transcribe_runs_whisper(self) -> None:
        backend = WhisperCppBackend(config={
            "model_path": self.model_path,
            "binary_path": self.binary_path,
            "threads": 1,
            "translate": True,
            "word_timestamps": True,
        })
        audio = np.ones(8_000, dtype=np.float32)
        fake_segment = TranscriptSegment(start=0.0, end=0.5, text="Hallo")
        with patch("app.backends.whisper_cpp_backend.subprocess.run") as mock_run, patch.object(
            WhisperCppBackend, "_load_transcript_text", return_value="Hallo"
        ) as mock_load, patch.object(
            WhisperCppBackend,
            "_parse_segment_file",
            return_value=[fake_segment],
        ) as mock_segments:
            result = backend.transcribe(audio=audio)
        self.assertEqual(result.text, "Hallo")
        mock_run.assert_called()
        mock_load.assert_called_once()
        mock_segments.assert_called_once()
        self.assertEqual(result.segments, [fake_segment])

    def test_transcribe_raises_when_model_missing(self) -> None:
        backend = WhisperCppBackend(config={
            "binary_path": self.binary_path,
            "auto_download_models": False,
        })
        with self.assertRaises(BackendConfigurationError):
            backend.transcribe(audio=np.zeros(1, dtype=np.float32))

    def test_model_downloads_when_missing(self) -> None:
        cache_dir = mkdtemp()
        backend = WhisperCppBackend(config={
            "model_cache_dir": cache_dir,
            "auto_download_models": True,
        })
        response = MagicMock()
        response.iter_content.return_value = [b"abc"]
        response.raise_for_status.return_value = None
        response.close = MagicMock()
        with patch("app.backends.whisper_cpp_backend.requests.get", return_value=response) as mock_get:
            model_path = backend._ensure_model_path_for_size("tiny")
        self.assertTrue(model_path.exists())
        self.assertGreater(model_path.stat().st_size, 0)
        mock_get.assert_called_once()
        shutil.rmtree(cache_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
