from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.settings import AppSettings, load_settings, save_settings


class AppSettingsTests(unittest.TestCase):
    def test_load_returns_defaults_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            with patch("app.settings.SETTINGS_PATH", settings_path):
                settings = load_settings()

        self.assertEqual(settings.backend, "faster_whisper")
        self.assertEqual(settings.backend_options, {})

    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            with patch("app.settings.SETTINGS_PATH", settings_path):
                save_settings(
                    AppSettings(
                        backend="whispercpp",
                        backend_options={"threads": "4", "use_vulkan": True},
                    )
                )
                loaded = load_settings()

        self.assertEqual(loaded.backend, "whispercpp")
        self.assertEqual(loaded.backend_options["threads"], "4")
        self.assertTrue(loaded.backend_options["use_vulkan"])

    def test_load_ignores_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings_path.write_text("{invalid", encoding="utf-8")
            with patch("app.settings.SETTINGS_PATH", settings_path):
                settings = load_settings()

        self.assertEqual(settings.backend, "faster_whisper")
        self.assertEqual(settings.backend_options, {})


if __name__ == "__main__":
    unittest.main()
