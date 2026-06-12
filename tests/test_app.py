from app import (
    format_log_line,
    greeting_delay_ms,
    is_app_shutdown_command,
    is_self_echo_transcript,
    is_spurious_auto_transcript,
    is_voice_stop_command,
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


def test_is_self_echo_transcript_blocks_hermes_prompt_inside_whisper_noise():
    assert (
        is_self_echo_transcript(
            "It's on your nails. Hi. What can I help you?",
            ("Hi, What Can I Help You?", "Anything else?"),
        )
        is True
    )


def test_is_self_echo_transcript_allows_real_user_command():
    assert (
        is_self_echo_transcript(
            "tolong buka youtube",
            ("Hi, What Can I Help You?", "Anything else?"),
        )
        is False
    )


def test_is_voice_stop_command_accepts_stop_with_or_without_wake_word():
    aliases = ("hey hermes", "hermes")

    assert is_voice_stop_command("stop", aliases) is True
    assert is_voice_stop_command("Hermes stop", aliases) is True
    assert is_voice_stop_command("hey hermes stop listening", aliases) is True
    assert is_voice_stop_command("Permit stop", aliases) is True
    assert is_voice_stop_command("please stop listening", aliases) is True


def test_is_voice_stop_command_rejects_unrelated_stop_phrases():
    assert is_voice_stop_command("open stopwatch", ("hermes",)) is False


def test_is_app_shutdown_command_accepts_quit_phrases():
    aliases = ("hey hermes", "hermes")

    assert is_app_shutdown_command("Hermes shutdown", aliases) is True
    assert is_app_shutdown_command("quit app", aliases) is True
    assert is_app_shutdown_command("exit hermes", aliases) is True
    assert is_app_shutdown_command("close this app", aliases) is True


def test_is_app_shutdown_command_rejects_regular_commands():
    assert is_app_shutdown_command("open youtube", ("hermes",)) is False


def test_is_spurious_auto_transcript_blocks_common_whisper_hallucinations():
    assert is_spurious_auto_transcript("You") is True
    assert is_spurious_auto_transcript("Thank you for watching.") is True
    assert is_spurious_auto_transcript("Thanks for watching!") is True


def test_is_spurious_auto_transcript_allows_actionable_commands():
    assert is_spurious_auto_transcript("open youtube") is False
    assert is_spurious_auto_transcript("buka google") is False
    assert is_spurious_auto_transcript("stop") is False
