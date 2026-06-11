from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread, current_thread
from time import monotonic
from typing import Any, Mapping

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot


def normalize_wake_name(name: str) -> str:
    return Path(name).stem.lower().replace(" ", "_").replace("-", "_")


def latest_score(raw_score: Any) -> float:
    score_array = np.asarray(raw_score, dtype=np.float32).reshape(-1)
    if score_array.size == 0:
        return 0.0
    return float(score_array[-1])


def wake_score(
    scores: Mapping[str, Any],
    aliases: tuple[str, ...],
    threshold: float,
) -> tuple[bool, str, float]:
    expected_names = {normalize_wake_name(alias) for alias in aliases}
    best_name = ""
    best_score = 0.0

    for raw_name, raw_score in scores.items():
        model_name = normalize_wake_name(raw_name)
        if not any(
            model_name == expected_name or model_name.startswith(f"{expected_name}_")
            for expected_name in expected_names
        ):
            continue
        score = latest_score(raw_score)
        if score > best_score:
            best_name = model_name
            best_score = score

    if best_score >= threshold:
        return True, best_name, best_score
    return False, "", 0.0


class OpenWakeWordDetector:
    def __init__(
        self,
        model_paths: tuple[str, ...],
        aliases: tuple[str, ...],
        threshold: float = 0.5,
        inference_framework: str = "onnx",
    ) -> None:
        self._model_paths = model_paths
        self._aliases = aliases
        self._threshold = threshold
        self._inference_framework = inference_framework
        self._model = None

    def predict(self, samples: np.ndarray) -> tuple[bool, str, float]:
        model = self._load_model()
        scores = model.predict(np.asarray(samples, dtype=np.int16).reshape(-1))
        return wake_score(scores, self._aliases, self._threshold)

    def _load_model(self):
        if self._model is None:
            from openwakeword.model import Model

            self._model = Model(
                wakeword_models=list(self._model_paths),
                inference_framework=self._inference_framework,
            )
        return self._model


class OpenWakeWordListener(QObject):
    wake_listening = Signal()
    wake_detected = Signal(str, float)
    wake_error = Signal(str)

    def __init__(
        self,
        model_paths: tuple[str, ...],
        aliases: tuple[str, ...],
        sample_rate: int = 16000,
        threshold: float = 0.5,
        debounce_seconds: float = 2.0,
        chunk_size: int = 1280,
        inference_framework: str = "onnx",
    ) -> None:
        super().__init__()
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._debounce_seconds = debounce_seconds
        self._detector = OpenWakeWordDetector(
            model_paths=model_paths,
            aliases=aliases,
            threshold=threshold,
            inference_framework=inference_framework,
        )
        self._audio_queue: Queue[np.ndarray] = Queue(maxsize=4)
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._last_detection_at = 0.0

    @Slot()
    def start_listening(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, name="OpenWakeWord", daemon=True)
        self._thread.start()

    @Slot()
    def stop_listening(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not current_thread():
            thread.join(timeout=1.5)

    def _run(self) -> None:
        try:
            self._detector._load_model()
        except Exception as exc:
            self.wake_error.emit(f"openWakeWord failed to load: {exc}")
            return

        try:
            import sounddevice as sd

            with sd.InputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self._chunk_size,
                callback=self._on_audio,
            ):
                self.wake_listening.emit()
                while not self._stop_event.is_set():
                    try:
                        chunk = self._audio_queue.get(timeout=0.2)
                    except Empty:
                        continue
                    detected, model_name, score = self._detector.predict(chunk)
                    now = monotonic()
                    if detected and now - self._last_detection_at >= self._debounce_seconds:
                        self._last_detection_at = now
                        self._stop_event.set()
                        self.wake_detected.emit(model_name, score)
                        return
        except Exception as exc:
            if not self._stop_event.is_set():
                self.wake_error.emit(f"openWakeWord listening failed: {exc}")

    def _on_audio(self, indata, frames, time, status) -> None:
        del frames, time
        if status:
            self.wake_error.emit(f"openWakeWord input warning: {status}")
        if self._stop_event.is_set():
            return
        try:
            self._audio_queue.put_nowait(np.asarray(indata, dtype=np.int16).copy())
        except Exception:
            pass
