from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class GuiSmokeTests(unittest.TestCase):
    def test_gui_and_entrypoint_modules_import(self) -> None:
        gui_module = importlib.import_module("app.gui")
        main_module = importlib.import_module("main")

        self.assertTrue(hasattr(gui_module, "AudioTranscriptionApp"))
        self.assertTrue(hasattr(main_module, "main"))


if __name__ == "__main__":
    unittest.main()
