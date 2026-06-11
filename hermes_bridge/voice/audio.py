from __future__ import annotations

from pathlib import Path
import wave

import numpy as np


def float32_to_pcm16(samples: np.ndarray) -> bytes:
    clipped = np.clip(samples.astype(np.float32), -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    return pcm.tobytes()


def write_wav(path: str | Path, samples: np.ndarray, sample_rate: int) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    flattened = np.asarray(samples, dtype=np.float32).reshape(-1)
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(float32_to_pcm16(flattened))

    return output_path
