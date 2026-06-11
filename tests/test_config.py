from pathlib import Path

import pytest

from hermes_bridge.config import ConfigError, load_settings


def write_env(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_settings_reads_discord_values(tmp_path: Path):
    env_file = write_env(
        tmp_path / ".env",
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=secret-token",
                "DISCORD_CHANNEL_ID=123456789",
                "DISCORD_APP_BOT_ID=987654321",
                "DISCORD_USER_ID=555555555",
                "WHISPER_MODEL_SIZE=small",
                "VOICE_SAMPLE_RATE=22050",
                "HERMES_TTS_ENABLED=false",
                "HERMES_WAKE_WORD=jarvis",
                "HERMES_WAKE_WORD_ALIASES=hey jarvis,jarvis",
                "HERMES_REQUIRE_WAKE_WORD=false",
                "HERMES_WAKE_BACKEND=openwakeword",
                "HERMES_OPENWAKEWORD_MODELS=models/hey_jarvis.onnx;models/jarvis.onnx",
                "HERMES_OPENWAKEWORD_THRESHOLD=0.7",
                "HERMES_OPENWAKEWORD_DEBOUNCE_SECONDS=1.5",
                "HERMES_OPENWAKEWORD_CHUNK_SIZE=960",
                "HERMES_OPENWAKEWORD_INFERENCE_FRAMEWORK=onnx",
                "HERMES_WAKE_GREETING=Ready.",
                "HERMES_REPLY_TIMEOUT_SECONDS=4.5",
                "HERMES_AUTO_VOICE_MAX_SECONDS=6.5",
                "HERMES_AUTO_VOICE_SILENCE_SECONDS=0.9",
                "HERMES_AUTO_VOICE_SILENCE_THRESHOLD=0.02",
            ]
        ),
    )

    settings = load_settings(env_file)

    assert settings.bot_token == "secret-token"
    assert settings.channel_id == 123456789
    assert settings.hermes_bot_id == 987654321
    assert settings.user_id == 555555555
    assert settings.bot_token_source == "DISCORD_BOT_TOKEN"
    assert settings.whisper_model_size == "small"
    assert settings.voice_sample_rate == 22050
    assert settings.tts_enabled is False
    assert settings.wake_word == "jarvis"
    assert settings.wake_word_aliases == ("hey jarvis", "jarvis")
    assert settings.require_wake_word is False
    assert settings.wake_backend == "openwakeword"
    assert settings.openwakeword_model_paths == (
        "models/hey_jarvis.onnx",
        "models/jarvis.onnx",
    )
    assert settings.openwakeword_threshold == 0.7
    assert settings.openwakeword_debounce_seconds == 1.5
    assert settings.openwakeword_chunk_size == 960
    assert settings.openwakeword_inference_framework == "onnx"
    assert settings.wake_greeting == "Ready."
    assert settings.reply_timeout_seconds == 4.5
    assert settings.auto_voice_max_seconds == 6.5
    assert settings.auto_voice_silence_seconds == 0.9
    assert settings.auto_voice_silence_threshold == 0.02


def test_load_settings_prefers_v2_bridge_token_when_present(tmp_path: Path):
    env_file = write_env(
        tmp_path / ".env",
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=hermes-agent-token",
                "DISCORD_BOT_TOKEN_V2=bridge-token",
                "DISCORD_CHANNEL_ID=123456789",
                "DISCORD_APP_BOT_ID=987654321",
            ]
        ),
    )

    settings = load_settings(env_file)

    assert settings.bot_token == "bridge-token"
    assert settings.bot_token_source == "DISCORD_BOT_TOKEN_V2"


def test_load_settings_reports_missing_required_values_without_token(tmp_path: Path):
    env_file = write_env(
        tmp_path / ".env",
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=super-secret-value",
                "DISCORD_APP_BOT_ID=987654321",
            ]
        ),
    )

    with pytest.raises(ConfigError) as exc_info:
        load_settings(env_file)

    message = str(exc_info.value)
    assert "DISCORD_CHANNEL_ID" in message
    assert "super-secret-value" not in message


def test_load_settings_rejects_non_numeric_ids(tmp_path: Path):
    env_file = write_env(
        tmp_path / ".env",
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=secret-token",
                "DISCORD_CHANNEL_ID=not-a-number",
                "DISCORD_APP_BOT_ID=987654321",
            ]
        ),
    )

    with pytest.raises(ConfigError) as exc_info:
        load_settings(env_file)

    assert "DISCORD_CHANNEL_ID must be numeric" in str(exc_info.value)


def test_load_settings_rejects_invalid_tts_enabled(tmp_path: Path):
    env_file = write_env(
        tmp_path / ".env",
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=secret-token",
                "DISCORD_CHANNEL_ID=123456789",
                "HERMES_TTS_ENABLED=maybe",
            ]
        ),
    )

    with pytest.raises(ConfigError) as exc_info:
        load_settings(env_file)

    assert "HERMES_TTS_ENABLED must be true or false" in str(exc_info.value)


def test_load_settings_rejects_non_numeric_user_id(tmp_path: Path):
    env_file = write_env(
        tmp_path / ".env",
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=secret-token",
                "DISCORD_CHANNEL_ID=123456789",
                "DISCORD_USER_ID=me",
            ]
        ),
    )

    with pytest.raises(ConfigError) as exc_info:
        load_settings(env_file)

    assert "DISCORD_USER_ID must be numeric" in str(exc_info.value)


def test_load_settings_uses_voice_defaults(tmp_path: Path):
    env_file = write_env(
        tmp_path / ".env",
        "\n".join(
            [
                "DISCORD_BOT_TOKEN=secret-token",
                "DISCORD_CHANNEL_ID=123456789",
            ]
        ),
    )

    settings = load_settings(env_file)

    assert settings.whisper_model_size == "tiny"
    assert settings.voice_sample_rate == 16000
    assert settings.tts_enabled is True
    assert settings.wake_word == "hermes"
    assert settings.wake_word_aliases == ("hey hermes", "hermes")
    assert settings.require_wake_word is True
    assert settings.wake_backend == "hybrid"
    assert settings.openwakeword_model_paths == ()
    assert settings.openwakeword_threshold == 0.35
    assert settings.openwakeword_debounce_seconds == 2.0
    assert settings.openwakeword_chunk_size == 1280
    assert settings.openwakeword_inference_framework == "onnx"
    assert settings.wake_greeting == "Hi, What Can I Help You?"
    assert settings.reply_timeout_seconds == 12.0
    assert settings.auto_voice_max_seconds == 8.0
    assert settings.auto_voice_silence_seconds == 1.2
    assert settings.auto_voice_silence_threshold == 0.012
