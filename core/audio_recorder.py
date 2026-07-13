"""Audio-Aufnahme vom Mikrofon und optional System-Audio (Loopback)."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000
CHANNELS = 1


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
        self._include_system_audio = False

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
        for index, info in enumerate(sd.query_devices()):
            if info["max_output_channels"] > 0:
                devices.append(
                    InputDevice(index=index, name=f"{info['name']} (System-Audio)")
                )
        return devices

    @staticmethod
    def loopback_supported() -> bool:
        return sys.platform == "win32" and bool(AudioRecorder.list_loopback_devices())

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def has_audio(self) -> bool:
        return bool(self._mic_frames)

    def get_audio(self) -> np.ndarray:
        mic = self._concat_frames(self._mic_frames)
        if not self._include_system_audio:
            return mic

        system = self._concat_frames(self._system_frames)
        if system.size == 0:
            return mic
        if mic.size == 0:
            return system
        return self._mix_audio(mic, system)

    def clear(self) -> None:
        self._mic_frames.clear()
        self._system_frames.clear()

    def start(self, config: RecordingConfig) -> None:
        if self._recording:
            return

        self.clear()
        self._include_system_audio = config.include_system_audio

        def mic_callback(indata: np.ndarray, _frames: int, _time, status) -> None:
            if status:
                print(f"Mikrofon-Status: {status}")
            self._mic_frames.append(indata.copy())

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

        self._recording = True

    def _start_loopback(self, output_device_index: int) -> None:
        extra_settings = None
        if sys.platform == "win32":
            extra_settings = sd.WasapiSettings(loopback=True)

        def system_callback(indata: np.ndarray, _frames: int, _time, status) -> None:
            if status:
                print(f"System-Audio-Status: {status}")
            mono = indata.mean(axis=1, keepdims=True) if indata.ndim > 1 else indata
            self._system_frames.append(mono.copy())

        self._system_stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=CHANNELS,
            dtype="float32",
            device=output_device_index,
            callback=system_callback,
            extra_settings=extra_settings,
        )
        self._system_stream.start()

    def stop(self) -> np.ndarray:
        if not self._recording:
            return self.get_audio()

        if self._mic_stream is not None:
            self._mic_stream.stop()
            self._mic_stream.close()
            self._mic_stream = None

        if self._system_stream is not None:
            self._system_stream.stop()
            self._system_stream.close()
            self._system_stream = None

        self._recording = False
        return self.get_audio()

    def duration_seconds(self) -> float:
        audio = self.get_audio()
        if audio.size == 0:
            return 0.0
        return len(audio) / self.sample_rate

    @staticmethod
    def _concat_frames(frames: list[np.ndarray]) -> np.ndarray:
        if not frames:
            return np.array([], dtype=np.float32)
        audio = np.concatenate(frames, axis=0)
        return np.squeeze(audio).astype(np.float32)

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
