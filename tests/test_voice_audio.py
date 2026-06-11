import wave

import numpy as np

from hermes_bridge.voice.audio import float32_to_pcm16, write_wav


def test_float32_to_pcm16_clips_and_converts_samples():
    samples = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)

    pcm = float32_to_pcm16(samples)
    converted = np.frombuffer(pcm, dtype=np.int16)

    assert converted.tolist() == [-32767, -32767, 0, 32767, 32767]


def test_write_wav_writes_mono_pcm16_file(tmp_path):
    wav_path = tmp_path / "command.wav"
    samples = np.array([0.0, 0.5, -0.5], dtype=np.float32)

    write_wav(wav_path, samples, sample_rate=16000)

    with wave.open(str(wav_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == 3
