from app import (
    format_log_line,
    greeting_delay_ms,
    parse_args,
    strip_wake_phrase,
    strip_wake_word,
)


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


def test_format_log_line_includes_timestamp_and_message():
    line = format_log_line("SYS: ready")

    assert line.endswith("SYS: ready")
    assert line.startswith("[")
    assert "] " in line


def test_greeting_delay_starts_command_capture_soon_after_wake_prompt():
    delay = greeting_delay_ms("Hi, What Can I Help You?")

    assert delay >= 1200
    assert delay <= 2500
