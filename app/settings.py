"""Persistente App-Einstellungen (z. B. gewünschtes Backend)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path.home() / ".audio_transcription_settings.json"


@dataclass
class AppSettings:
    backend: str = "faster_whisper"
    backend_options: dict[str, Any] = field(default_factory=dict)


def load_settings() -> AppSettings:
    try:
        raw = _CONFIG_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return AppSettings()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return AppSettings()
    return AppSettings(
        backend=data.get("backend", "faster_whisper"),
        backend_options=data.get("backend_options", {}),
    )


def save_settings(settings: AppSettings) -> None:
    _CONFIG_PATH.write_text(
        json.dumps(
            {
                "backend": settings.backend,
                "backend_options": settings.backend_options,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
