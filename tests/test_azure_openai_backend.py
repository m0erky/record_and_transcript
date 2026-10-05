from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from app.backends.azure_openai_backend import AzureOpenAIBackend


class AzureOpenAIBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "endpoint": "https://example.azure.com",
            "api_key": "secret",
            "deployment": "gpt-4o-transcribe",
            "api_version": "2023-05-15",
            "timeout": 5,
        }
        self.audio = np.ones(16_000, dtype=np.float32)

    def test_initialize_raises_when_config_missing(self) -> None:
        backend = AzureOpenAIBackend(config={})
        with self.assertRaises(RuntimeError):
            backend.initialize()

    @patch("app.backends.azure_openai_backend.requests.post")
    def test_transcribe_posts_audio_and_returns_text(self, mock_post: MagicMock) -> None:
        backend = AzureOpenAIBackend(config=self.config)
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"text": "Hallo Welt", "language": "de"}
        mock_post.return_value = response

        result = backend.transcribe(audio=self.audio)

        self.assertEqual(result.text, "Hallo Welt")
        self.assertEqual(result.language, "de")
        called_args, called_kwargs = mock_post.call_args
        self.assertTrue(called_args)
        self.assertIn("/openai/deployments/gpt-4o-transcribe/audio/transcriptions", called_args[0])
        self.assertIn("headers", called_kwargs)
        self.assertEqual(called_kwargs["headers"], {"api-key": "secret"})
        self.assertIn("files", called_kwargs)
        self.assertIn("file", called_kwargs["files"])

    @patch("app.backends.azure_openai_backend.requests.post")
    def test_transcribe_raises_when_status_not_ok(self, mock_post: MagicMock) -> None:
        backend = AzureOpenAIBackend(config=self.config)
        response = MagicMock()
        response.status_code = 500
        response.text = "oops"
        mock_post.return_value = response

        with self.assertRaises(RuntimeError):
            backend.transcribe(audio=self.audio)


if __name__ == "__main__":
    unittest.main()
