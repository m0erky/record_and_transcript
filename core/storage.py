"""Speichern von Aufnahmen und Transkripten."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf

from core.docx_exporter import default_title, export_to_docx


@dataclass
class SessionPaths:
    folder: Path
    raw_recording: Path
    enhanced_recording: Path
    transcript_txt: Path
    transcript_docx: Path


class SessionStorage:
    def __init__(self, base_dir: Path | None = None) -> None:
        root = base_dir or Path(__file__).resolve().parent.parent / "output" / "sessions"
        self.base_dir = root
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._current_session: SessionPaths | None = None

    def create_session(self) -> SessionPaths:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = self.base_dir / timestamp
        folder.mkdir(parents=True, exist_ok=True)

        self._current_session = SessionPaths(
            folder=folder,
            raw_recording=folder / "recording_raw.wav",
            enhanced_recording=folder / "recording_enhanced.wav",
            transcript_txt=folder / "transcript.txt",
            transcript_docx=folder / "transcript.docx",
        )
        return self._current_session

    @property
    def current_session(self) -> SessionPaths | None:
        return self._current_session

    def save_wav(self, path: Path, audio: np.ndarray, sample_rate: int) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), audio, sample_rate, subtype="PCM_16")
        return path

    def save_transcript_txt(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def save_transcript_docx(
        self,
        path: Path,
        text: str,
        metadata: dict[str, str] | None = None,
    ) -> Path:
        return export_to_docx(
            text=text,
            output_path=path,
            title=default_title(),
            metadata=metadata,
        )

    def save_all(
        self,
        raw_audio: np.ndarray,
        enhanced_audio: np.ndarray | None,
        transcript: str,
        sample_rate: int,
        metadata: dict[str, str] | None = None,
    ) -> SessionPaths:
        session = self.create_session()
        self.save_wav(session.raw_recording, raw_audio, sample_rate)

        if enhanced_audio is not None:
            self.save_wav(session.enhanced_recording, enhanced_audio, sample_rate)

        self.save_transcript_txt(session.transcript_txt, transcript)
        self.save_transcript_docx(session.transcript_docx, transcript, metadata)
        return session
