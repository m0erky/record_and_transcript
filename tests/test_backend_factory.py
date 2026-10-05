from __future__ import annotations

import unittest

from app.backends.azure_openai_backend import AzureOpenAIBackend
from app.backends.factory import BackendFactory
from app.backends.openai_backend import OpenAIBackend
from app.backends.whisper_cpp_backend import WhisperCppBackend


class BackendFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = BackendFactory()

    def test_create_default_backend(self) -> None:
        backend = self.factory.create_backend()
        self.assertTrue(hasattr(backend, "transcribe"))

    def test_create_specific_backend(self) -> None:
        backend = self.factory.create_backend(
            {
                "backend": "azure_openai",
                "options": {
                    "endpoint": "https://example.azure.com",
                    "api_key": "key",
                    "deployment": "my-deploy",
                },
            }
        )
        self.assertIsInstance(backend, AzureOpenAIBackend)

    def test_create_short_alias(self) -> None:
        backend = self.factory.create_backend(
            {"backend": "whispercpp"}
        )
        self.assertIsInstance(backend, WhisperCppBackend)

    def test_unknown_backend_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.factory.create_backend({"backend": "unknown"})

    def test_openai_backend_options_passed(self) -> None:
        backend = self.factory.create_backend({"backend": "openai", "options": {"api_key": "xyz"}})
        self.assertIsInstance(backend, OpenAIBackend)
        self.assertEqual(backend._api_config.api_key, "xyz")


if __name__ == "__main__":
    unittest.main()
