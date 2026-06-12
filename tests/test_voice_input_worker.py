import numpy as np

from hermes_bridge.voice.input_worker import VoiceInputWorker


class FakeStream:
    def __init__(self) -> None:
        self.stopped = False
        self.closed = False

    def stop(self) -> None:
        self.stopped = True

    def close(self) -> None:
        self.closed = True


def test_cancel_recording_drops_audio_without_transcribing():
    worker = VoiceInputWorker()
    stream = FakeStream()
    transcribed_chunks = []
    worker._is_recording = True
    worker._stream = stream
    worker._chunks = [np.array([0.2], dtype=np.float32)]
    worker._transcribe_chunks = transcribed_chunks.append

    worker.cancel_recording()

    assert stream.stopped is True
    assert stream.closed is True
    assert worker._is_recording is False
    assert worker._chunks == []
    assert transcribed_chunks == []
