from app import strip_wake_word


def test_strip_wake_word_removes_wake_word_and_punctuation():
    assert strip_wake_word("Hermes, buka chrome", "hermes") == "buka chrome"
    assert strip_wake_word("Hey Hermes!", "hermes") == ""


def test_strip_wake_word_accepts_wake_word_in_sentence():
    assert strip_wake_word("tolong Hermes cek cuaca", "hermes") == "tolong cek cuaca"


def test_strip_wake_word_accepts_common_misrecognitions():
    assert strip_wake_word("hey ermes buka chrome", "hermes") == "buka chrome"
    assert strip_wake_word("her miss open settings", "hermes") == "open settings"
    assert strip_wake_word("harness wake up", "hermes") == "wake up"


def test_strip_wake_word_returns_none_when_missing():
    assert strip_wake_word("buka chrome", "hermes") is None
