from types import SimpleNamespace

from hermes_bridge.voice.transcriber import WhisperTranscriber, normalize_segments


def test_normalize_segments_joins_and_strips_text():
    segments = [
        SimpleNamespace(text="  buka "),
        SimpleNamespace(text=" chrome  "),
    ]

    assert normalize_segments(segments) == "buka chrome"


def test_normalize_segments_removes_empty_segments():
    segments = [
        SimpleNamespace(text=" "),
        SimpleNamespace(text="  apa kabar "),
        SimpleNamespace(text=""),
    ]

    assert normalize_segments(segments) == "apa kabar"


def test_transcribe_uses_vad_and_disables_previous_text_conditioning(tmp_path):
    class FakeModel:
        def __init__(self) -> None:
            self.kwargs = None

        def transcribe(self, audio_path, **kwargs):
            self.kwargs = kwargs
            return [SimpleNamespace(text=" buka youtube ")], SimpleNamespace()

    model = FakeModel()
    transcriber = WhisperTranscriber()
    transcriber._model = model

    transcript = transcriber.transcribe(tmp_path / "voice.wav")

    assert transcript == "buka youtube"
    assert model.kwargs["beam_size"] == 1
    assert model.kwargs["vad_filter"] is True
    assert model.kwargs["condition_on_previous_text"] is False
