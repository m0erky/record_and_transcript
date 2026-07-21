from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

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
        with patch("app.backends.whisper_cpp_backend.subprocess.run") as mock_run, patch.object(
            WhisperCppBackend, "_load_transcript_text", return_value="Hallo"
        ) as mock_load:
            result = backend.transcribe(audio=audio)
        self.assertEqual(result.text, "Hallo")
        mock_run.assert_called()
        mock_load.assert_called_once()

    def test_transcribe_raises_when_model_missing(self) -> None:
        backend = WhisperCppBackend(config={"binary_path": self.binary_path})
        with self.assertRaises(RuntimeError):
            backend.transcribe(audio=np.zeros(1, dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
