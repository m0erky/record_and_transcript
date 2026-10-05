"""Persistente App-Einstellungen (z.B. gewünschtes Backend)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppSettings:
    backend: str = "faster_whisper"
    backend_options: dict[str, Any] = field(default_factory=dict)


def load_settings() -> AppSettings:
    """Return default application settings that are configured in code."""
    return AppSettings()


def save_settings(settings: AppSettings) -> None:
    """Settings are not persisted to disk any more."""
    return None
