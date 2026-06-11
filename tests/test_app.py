from app import parse_args, strip_wake_phrase, strip_wake_word


def test_strip_wake_word_removes_wake_word_and_punctuation():
    assert strip_wake_word("Hermes, buka chrome", "hermes") == "buka chrome"


def test_strip_wake_word_accepts_wake_word_in_sentence():
    assert strip_wake_word("tolong Hermes cek cuaca", "hermes") == "tolong cek cuaca"


def test_strip_wake_word_returns_none_when_missing():
    assert strip_wake_word("buka chrome", "hermes") is None


def test_strip_wake_phrase_prefers_longest_phrase():
    assert strip_wake_phrase("Hey Hermes!", ("hermes", "hey hermes")) == ""


def test_strip_wake_phrase_accepts_short_alias():
    assert strip_wake_phrase("Hermes, buka chrome", ("hey hermes", "hermes")) == "buka chrome"


def test_parse_args_accepts_start_hidden_voice_mode():
    args = parse_args(["--start-hidden", "--voice-mode"])

    assert args.start_hidden is True
    assert args.voice_mode is True
