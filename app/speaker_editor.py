"""Hilfsfunktionen für Sprecher-Operationen auf Transcript-Segmenten."""

from __future__ import annotations

from app.backends.base import TranscriptSegment


def speaker_names_from_segments(segments: list[TranscriptSegment]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for segment in segments:
        if not segment.speaker:
            continue
        if segment.speaker in seen:
            continue
        seen.add(segment.speaker)
        names.append(segment.speaker)
    return names


def rename_speaker_in_segments(
    segments: list[TranscriptSegment],
    *,
    old_name: str,
    new_name: str,
) -> list[TranscriptSegment]:
    renamed: list[TranscriptSegment] = []
    for segment in segments:
        speaker = new_name if segment.speaker == old_name else segment.speaker
        renamed.append(
            TranscriptSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                speaker=speaker,
                speaker_confidence=segment.speaker_confidence,
            )
        )
    return renamed


def merge_speakers_in_segments(
    segments: list[TranscriptSegment],
    *,
    source_name: str,
    target_name: str,
) -> list[TranscriptSegment]:
    return rename_speaker_in_segments(segments, old_name=source_name, new_name=target_name)


def compose_transcript_text_from_segments(segments: list[TranscriptSegment]) -> str:
    if not segments:
        return ""
    if any(segment.speaker for segment in segments):
        return "\n\n".join(
            f"{segment.speaker or 'Sprecher ?'} [{_format_timestamp(segment.start)} - {_format_timestamp(segment.end)}]: {segment.text}"
            for segment in segments
        ).strip()
    return " ".join(segment.text for segment in segments).strip()


def _format_timestamp(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"
