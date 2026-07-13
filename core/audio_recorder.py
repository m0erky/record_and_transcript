"""Audio-Aufnahme vom Mikrofon und optional System-Audio (Loopback)."""

from __future__ import annotations

import math
import sys
import threading
from dataclasses import dataclass
from os import PathLike
from typing import Any

import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import resample_poly

try:
    import soundcard as sc
except ImportError:
    sc = None

SAMPLE_RATE = 16_000
CHANNELS = 1
SOUNDCARD_LOOPBACK_BASE = 10_000
SOUNDDEVICE_SYSTEM_INPUT_BASE = 20_000
SYSTEM_INPUT_KEYWORDS = (
    "stereo mix",
    "what u hear",
    "wave out",
    "loopback",
    "mixage",
)


@dataclass
class InputDevice:
    index: int
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class RecordingConfig:
    mic_device_index: int
    include_system_audio: bool = False
    loopback_device_index: int | None = None


class AudioRecorder:
    def __init__(self, sample_rate: int = SAMPLE_RATE) -> None:
        self.sample_rate = sample_rate
        self._mic_frames: list[np.ndarray] = []
        self._system_frames: list[np.ndarray] = []
        self._mic_stream: sd.InputStream | None = None
        self._system_stream: sd.InputStream | None = None
        self._recording = False
        self._paused = False
        self._include_system_audio = False
        self._system_sample_rate = sample_rate
        self._system_thread: threading.Thread | None = None
        self._system_stop_event = threading.Event()
        self._system_error: str | None = None

    @staticmethod
    def list_input_devices() -> list[InputDevice]:
        devices: list[InputDevice] = []
        for index, info in enumerate(sd.query_devices()):
            if info["max_input_channels"] > 0:
                devices.append(InputDevice(index=index, name=info["name"]))
        return devices

    @staticmethod
    def list_loopback_devices() -> list[InputDevice]:
        if sys.platform != "win32":
            return []

        devices: list[InputDevice] = []

        for index, speaker in enumerate(AudioRecorder._list_soundcard_speakers()):
            devices.append(
                InputDevice(
                    index=SOUNDCARD_LOOPBACK_BASE + index,
                    name=f"{AudioRecorder._soundcard_display_name(speaker)} (System-Audio)",
                )
            )

        for index, info in enumerate(sd.query_devices()):
            name = str(info["name"])
            if info["max_input_channels"] > 0 and AudioRecorder._looks_like_system_input(name):
                devices.append(
                    InputDevice(
                        index=SOUNDDEVICE_SYSTEM_INPUT_BASE + index,
                        name=f"{name} (System-Audio Eingang)",
                    )
                )

        return devices

    @staticmethod
    def loopback_supported() -> bool:
        return sys.platform == "win32" and bool(AudioRecorder.list_loopback_devices())

    @staticmethod
    def load_audio_file(
        path: str | PathLike[str],
        target_sample_rate: int = SAMPLE_RATE,
    ) -> np.ndarray:
        audio, source_sample_rate = sf.read(str(path), dtype="float32", always_2d=False)
        prepared = np.asarray(audio, dtype=np.float32)
        if prepared.ndim > 1:
            prepared = prepared.mean(axis=1)
        else:
            prepared = np.squeeze(prepared)

        if prepared.size == 0:
            return np.array([], dtype=np.float32)

        peak = float(np.max(np.abs(prepared)))
        if peak > 1.0:
            prepared = prepared / peak

        return AudioRecorder._resample_audio(prepared, int(source_sample_rate), target_sample_rate)

    @staticmethod
    def _list_soundcard_speakers() -> list[Any]:
        if sys.platform != "win32" or sc is None:
            return []
        try:
            return list(sc.all_speakers())
        except Exception:
            return []

    @staticmethod
    def _soundcard_display_name(device: Any) -> str:
        for attr in ("name", "id"):
            value = getattr(device, attr, None)
            if value:
                return str(value)
        return str(device)

    @staticmethod
    def _looks_like_system_input(device_name: str) -> bool:
        name = device_name.casefold()
        return any(keyword in name for keyword in SYSTEM_INPUT_KEYWORDS)

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def is_paused(self) -> bool:
        return self._recording and self._paused

    @property
    def has_audio(self) -> bool:
        return bool(self._mic_frames)

    def get_audio(self) -> np.ndarray:
        mic = self._concat_mono_frames(self._mic_frames)
        if not self._include_system_audio:
            return mic

        system = self._prepare_system_audio()
        if system.size == 0:
            return mic
        if mic.size == 0:
            return system
        return self._mix_audio(mic, system)

    def clear(self) -> None:
        self._mic_frames.clear()
        self._system_frames.clear()
        self._system_sample_rate = self.sample_rate
        self._system_error = None
        self._paused = False

    def start(self, config: RecordingConfig) -> None:
        if self._recording:
            return

        self.clear()
        self._include_system_audio = config.include_system_audio

        def mic_callback(indata: np.ndarray, _frames: int, _time, status) -> None:
            if status:
                print(f"Mikrofon-Status: {status}")
            if self._paused:
                return
            self._mic_frames.append(indata.copy())

        try:
            self._mic_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=CHANNELS,
                dtype="float32",
                device=config.mic_device_index,
                callback=mic_callback,
            )
            self._mic_stream.start()

            if config.include_system_audio and config.loopback_device_index is not None:
                self._start_loopback(config.loopback_device_index)
        except Exception:
            self._close_streams()
            self.clear()
            self._recording = False
            raise

        self._recording = True
        self._paused = False

    def pause(self) -> None:
        if self._recording:
            self._paused = True

    def resume(self) -> None:
        if self._recording:
            self._paused = False

    def _start_loopback(self, device_index: int) -> None:
        if sys.platform != "win32":
            raise RuntimeError("System-Audio-Aufnahme wird nur unter Windows unterstützt.")

        if SOUNDCARD_LOOPBACK_BASE <= device_index < SOUNDDEVICE_SYSTEM_INPUT_BASE:
            self._start_soundcard_loopback(device_index - SOUNDCARD_LOOPBACK_BASE)
            return

        if device_index >= SOUNDDEVICE_SYSTEM_INPUT_BASE:
            sounddevice_index = device_index - SOUNDDEVICE_SYSTEM_INPUT_BASE
            device_info = sd.query_devices(sounddevice_index)
            self._start_system_input_device(sounddevice_index, device_info)
            return

        raise RuntimeError("Ungültiges System-Audio-Gerät ausgewählt.")

    def _start_soundcard_loopback(self, speaker_list_index: int) -> None:
        if sc is None:
            raise RuntimeError(
                "Das Python-Paket 'soundcard' ist nicht installiert. "
                "Bitte installiere es mit: pip install soundcard"
            )

        speakers = self._list_soundcard_speakers()
        if not speakers:
            raise RuntimeError("Keine System-Audio-Geräte über soundcard gefunden.")
        if speaker_list_index < 0 or speaker_list_index >= len(speakers):
            raise RuntimeError("Das gewählte soundcard-Systemgerät ist nicht mehr verfügbar.")

        speaker = speakers[speaker_list_index]
        speaker_name = self._soundcard_display_name(speaker)
        samplerate = self._guess_output_samplerate(speaker_name)
        self._system_sample_rate = samplerate
        self._system_error = None
        self._system_stop_event.clear()

        self._system_thread = threading.Thread(
            target=self._capture_soundcard_loopback,
            args=(speaker, samplerate),
            daemon=True,
        )
        self._system_thread.start()
        self._system_thread.join(timeout=0.2)

        if self._system_error is not None:
            error_message = self._system_error
            self._close_system_thread()
            raise RuntimeError(error_message)

    def _capture_soundcard_loopback(self, speaker: Any, samplerate: int) -> None:
        speaker_name = self._soundcard_display_name(speaker)
        chunk_frames = max(512, samplerate // 20)

        try:
            recorder_context = self._create_soundcard_recorder(speaker, samplerate)
            with recorder_context as recorder:
                while not self._system_stop_event.is_set():
                    data = recorder.record(numframes=chunk_frames)
                    if self._paused:
                        continue
                    audio = np.asarray(data, dtype=np.float32)
                    if audio.size == 0:
                        continue
                    self._system_frames.append(audio.copy())
        except Exception as exc:
            self._system_error = (
                "System-Audio über soundcard konnte nicht gestartet werden. "
                f"Gerät: {speaker_name}, Samplerate: {samplerate} Hz. "
                f"Originalfehler: {exc}"
            )
            self._system_stop_event.set()

    def _create_soundcard_recorder(self, speaker: Any, samplerate: int):
        if hasattr(speaker, "recorder"):
            for kwargs in (
                {"samplerate": samplerate},
                {"samplerate": samplerate, "channels": None},
                {},
            ):
                try:
                    return speaker.recorder(**kwargs)
                except TypeError:
                    continue

        microphone = self._resolve_soundcard_loopback_microphone(speaker)
        for kwargs in (
            {"samplerate": samplerate},
            {"samplerate": samplerate, "channels": None},
            {},
        ):
            try:
                return microphone.recorder(**kwargs)
            except TypeError:
                continue

        raise RuntimeError("soundcard konnte keinen Recorder für das gewählte Systemgerät erzeugen.")

    def _resolve_soundcard_loopback_microphone(self, speaker: Any):
        if sc is None:
            raise RuntimeError("soundcard ist nicht installiert.")

        candidates: list[str] = []
        for attr in ("id", "name"):
            value = getattr(speaker, attr, None)
            if value:
                candidates.append(str(value))
        candidates.append(str(speaker))

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                microphone = sc.get_microphone(candidate, include_loopback=True)
                if microphone is not None:
                    return microphone
            except Exception as exc:
                last_error = exc

        raise RuntimeError(
            "Es konnte kein Loopback-Mikrofon für das gewählte soundcard-Gerät gefunden werden."
        ) from last_error

    def _start_system_input_device(self, device_index: int, device_info) -> None:
        samplerate = int(round(float(device_info.get("default_samplerate", self.sample_rate))))
        channels = int(device_info.get("max_input_channels", CHANNELS)) or CHANNELS
        if samplerate <= 0:
            samplerate = self.sample_rate
        if channels <= 0:
            channels = CHANNELS

        self._system_sample_rate = samplerate

        def system_callback(indata: np.ndarray, _frames: int, _time, status) -> None:
            if status:
                print(f"System-Audio-Status: {status}")
            if self._paused:
                return
            self._system_frames.append(indata.copy())

        try:
            self._system_stream = sd.InputStream(
                samplerate=samplerate,
                channels=channels,
                dtype="float32",
                device=device_index,
                callback=system_callback,
            )
            self._system_stream.start()
        except Exception as exc:
            raise RuntimeError(
                "System-Audio-Eingang konnte nicht gestartet werden. "
                f"Gerät: {device_info['name']}, Samplerate: {samplerate} Hz, Kanäle: {channels}. "
                f"Originalfehler: {exc}"
            ) from exc

    def stop(self) -> np.ndarray:
        if not self._recording:
            return self.get_audio()

        self._close_streams()
        self._recording = False
        self._paused = False
        return self.get_audio()

    def duration_seconds(self) -> float:
        audio = self.get_audio()
        if audio.size == 0:
            return 0.0
        return len(audio) / self.sample_rate

    def _close_streams(self) -> None:
        if self._mic_stream is not None:
            try:
                self._mic_stream.stop()
            except Exception:
                pass
            try:
                self._mic_stream.close()
            except Exception:
                pass
            self._mic_stream = None

        if self._system_stream is not None:
            try:
                self._system_stream.stop()
            except Exception:
                pass
            try:
                self._system_stream.close()
            except Exception:
                pass
            self._system_stream = None

        self._close_system_thread()

    def _close_system_thread(self) -> None:
        self._system_stop_event.set()
        if self._system_thread is not None:
            self._system_thread.join(timeout=1.0)
            self._system_thread = None
        self._system_stop_event.clear()

    def _prepare_system_audio(self) -> np.ndarray:
        if not self._system_frames:
            return np.array([], dtype=np.float32)

        audio = np.concatenate(self._system_frames, axis=0).astype(np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        else:
            audio = np.squeeze(audio)

        return self._resample_audio(audio, self._system_sample_rate, self.sample_rate)

    @staticmethod
    def _guess_output_samplerate(device_name: str) -> int:
        for info in sd.query_devices():
            if info["max_output_channels"] <= 0:
                continue
            if str(info["name"]).casefold() != device_name.casefold():
                continue
            samplerate = int(round(float(info.get("default_samplerate", 48_000))))
            if samplerate > 0:
                return samplerate
        return 48_000

    @staticmethod
    def _concat_mono_frames(frames: list[np.ndarray]) -> np.ndarray:
        if not frames:
            return np.array([], dtype=np.float32)
        audio = np.concatenate(frames, axis=0)
        return np.squeeze(audio).astype(np.float32)

    @staticmethod
    def _resample_audio(
        audio: np.ndarray,
        source_sample_rate: int,
        target_sample_rate: int,
    ) -> np.ndarray:
        if audio.size == 0 or source_sample_rate == target_sample_rate:
            return audio.astype(np.float32)

        divisor = math.gcd(int(source_sample_rate), int(target_sample_rate))
        up = target_sample_rate // divisor
        down = source_sample_rate // divisor
        resampled = resample_poly(audio, up, down)
        return resampled.astype(np.float32)

    @staticmethod
    def _mix_audio(mic: np.ndarray, system: np.ndarray) -> np.ndarray:

        max_len = max(len(mic), len(system))
        if len(mic) < max_len:
            mic = np.pad(mic, (0, max_len - len(mic)))
        if len(system) < max_len:
            system = np.pad(system, (0, max_len - len(system)))

        mixed = 0.5 * mic + 0.5 * system
        peak = float(np.max(np.abs(mixed)))
        if peak > 1.0:
            mixed = mixed / peak
        return mixed.astype(np.float32)





