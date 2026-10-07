"""Persistente App-Einstellungen (z.B. gewünschtes Backend)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SETTINGS_PATH = Path.home() / ".audio_transcription_settings.json"


@dataclass
class AppSettings:
    backend: str = "faster_whisper"
    backend_options: dict[str, Any] = field(default_factory=dict)


def load_settings() -> AppSettings:
    if not SETTINGS_PATH.exists():
        return AppSettings()
    try:
        raw_data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppSettings()
    backend = raw_data.get("backend") if isinstance(raw_data, dict) else None
    backend_options = raw_data.get("backend_options") if isinstance(raw_data, dict) else None
    return AppSettings(
        backend=backend if isinstance(backend, str) and backend.strip() else "faster_whisper",
        backend_options=backend_options if isinstance(backend_options, dict) else {},
    )


def save_settings(settings: AppSettings) -> None:
    payload = {
        "backend": settings.backend,
        "backend_options": settings.backend_options,
    }
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
