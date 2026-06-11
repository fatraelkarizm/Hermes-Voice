from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir
from threading import Lock, Thread, Timer
from time import monotonic
from uuid import uuid4

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from hermes_bridge.voice.audio import write_wav
from hermes_bridge.voice.transcriber import WhisperTranscriber


class VoiceInputWorker(QObject):
    recording_started = Signal()
    transcribing_started = Signal()
    transcript_ready = Signal(str)
    voice_error = Signal(str)

    def __init__(self, sample_rate: int = 16000, model_size: str = "tiny"):
        super().__init__()
        self._sample_rate = sample_rate
        self._transcriber = WhisperTranscriber(model_size=model_size)
        self._stream = None
        self._chunks: list[np.ndarray] = []
        self._is_recording = False
        self._auto_stop_timer: Timer | None = None
        self._auto_stop_requested = False
        self._is_auto_recording = False
        self._recording_started_at = 0.0
        self._last_voice_at = 0.0
        self._min_auto_recording_seconds = 0.8
        self._auto_silence_seconds = 1.2
        self._auto_silence_threshold = 0.012
        self._lock = Lock()

    @Slot()
    def start_recording(self) -> None:
        self._start_recording(auto=False)

    @Slot()
    def start_auto_recording(
        self,
        max_seconds: float = 8.0,
        silence_seconds: float = 1.2,
        silence_threshold: float = 0.012,
    ) -> None:
        self._auto_silence_seconds = silence_seconds
        self._auto_silence_threshold = silence_threshold
        if self._start_recording(auto=True):
            self._auto_stop_timer = Timer(max_seconds, self.stop_recording)
            self._auto_stop_timer.daemon = True
            self._auto_stop_timer.start()

    def _start_recording(self, auto: bool) -> bool:
        with self._lock:
            if self._is_recording:
                return False

            self._chunks.clear()
            self._auto_stop_requested = False
            self._is_auto_recording = auto
            self._recording_started_at = monotonic()
            self._last_voice_at = 0.0

            try:
                import sounddevice as sd

                self._stream = sd.InputStream(
                    samplerate=self._sample_rate,
                    channels=1,
                    dtype="float32",
                    callback=self._on_audio,
                )
                self._stream.start()
                self._is_recording = True
                self.recording_started.emit()
                return True
            except Exception as exc:
                self._is_recording = False
                self._is_auto_recording = False
                self.voice_error.emit(f"Voice recording failed: {exc}")
                return False

    @Slot()
    def stop_recording(self) -> None:
        with self._lock:
            if not self._is_recording:
                return

            self._is_recording = False
            if self._auto_stop_timer is not None:
                self._auto_stop_timer.cancel()
                self._auto_stop_timer = None

            stream = self._stream
            self._stream = None
            self._is_auto_recording = False
            chunks = [chunk.copy() for chunk in self._chunks]
            self._chunks.clear()

        try:
            if stream is not None:
                stream.stop()
                stream.close()
        except Exception as exc:
            self.voice_error.emit(f"Voice stop failed: {exc}")
            return

        Thread(target=self._transcribe_chunks, args=(chunks,), daemon=True).start()

    def _on_audio(self, indata, frames, time, status) -> None:
        del frames, time
        if status:
            self.voice_error.emit(f"Voice input warning: {status}")
        chunk = np.asarray(indata, dtype=np.float32).copy()
        with self._lock:
            if not self._is_recording:
                return
            self._chunks.append(chunk)
            if not self._is_auto_recording:
                return

            now = monotonic()
            rms = float(np.sqrt(np.mean(np.square(chunk)))) if chunk.size else 0.0
            if rms >= self._auto_silence_threshold:
                self._last_voice_at = now
                return

            started_long_enough = (
                now - self._recording_started_at >= self._min_auto_recording_seconds
            )
            heard_voice = self._last_voice_at > 0
            silent_long_enough = now - self._last_voice_at >= self._auto_silence_seconds
            if (
                started_long_enough
                and heard_voice
                and silent_long_enough
                and not self._auto_stop_requested
            ):
                self._auto_stop_requested = True
                Thread(target=self.stop_recording, daemon=True).start()

    def _transcribe_chunks(self, chunks: list[np.ndarray]) -> None:
        if not chunks:
            self.voice_error.emit("No voice audio captured.")
            return

        self.transcribing_started.emit()
        try:
            samples = np.concatenate(chunks, axis=0).reshape(-1)
            wav_path = Path(gettempdir()) / f"hermes-voice-{uuid4().hex}.wav"
            write_wav(wav_path, samples, self._sample_rate)
            transcript = self._transcriber.transcribe(wav_path)
            try:
                wav_path.unlink(missing_ok=True)
            except OSError:
                pass
        except Exception as exc:
            self.voice_error.emit(f"Voice transcription failed: {exc}")
            return

        if not transcript:
            self.voice_error.emit("No speech detected.")
            return

        self.transcript_ready.emit(transcript)
