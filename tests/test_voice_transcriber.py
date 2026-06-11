from types import SimpleNamespace

from hermes_bridge.voice.transcriber import normalize_segments


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
