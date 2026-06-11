from __future__ import annotations

from pathlib import Path
from typing import Iterable, Protocol


class WhisperSegment(Protocol):
    text: str


def normalize_segments(segments: Iterable[WhisperSegment]) -> str:
    parts = [segment.text.strip() for segment in segments if segment.text.strip()]
    return " ".join(parts).strip()


class WhisperTranscriber:
    def __init__(
        self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"
    ):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None

    def transcribe(self, audio_path: str | Path) -> str:
        model = self._load_model()
        segments, _info = model.transcribe(
            str(audio_path),
            beam_size=1,
            condition_on_previous_text=False,
            initial_prompt="The wake word is Hermes. The user may say Hey Hermes.",
        )
        return normalize_segments(segments)

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
        return self._model
