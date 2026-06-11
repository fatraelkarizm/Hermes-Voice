from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """Raised when Hermes bridge configuration is missing or invalid."""


@dataclass(frozen=True)
class DiscordSettings:
    bot_token: str
    channel_id: int
    hermes_bot_id: int | None = None
    user_id: int | None = None
    bot_token_source: str = "DISCORD_BOT_TOKEN"
    whisper_model_size: str = "tiny"
    voice_sample_rate: int = 16000
    tts_enabled: bool = True
    wake_word: str = "hermes"
    require_wake_word: bool = True
    auto_voice_max_seconds: float = 8.0
    auto_voice_silence_seconds: float = 1.2
    auto_voice_silence_threshold: float = 0.012


def load_settings(env_path: str | Path = ".env") -> DiscordSettings:
    values = _read_env_file(Path(env_path))

    bot_token_v2 = values.get("DISCORD_BOT_TOKEN_V2", "").strip()
    bot_token_v1 = values.get("DISCORD_BOT_TOKEN", "").strip()
    bot_token = bot_token_v2 or bot_token_v1
    bot_token_source = "DISCORD_BOT_TOKEN_V2" if bot_token_v2 else "DISCORD_BOT_TOKEN"
    channel_id_text = values.get("DISCORD_CHANNEL_ID", "").strip()
    hermes_bot_id_text = values.get("DISCORD_APP_BOT_ID", "").strip()
    user_id_text = values.get("DISCORD_USER_ID", "").strip()
    whisper_model_size = values.get("WHISPER_MODEL_SIZE", "tiny").strip() or "tiny"
    voice_sample_rate_text = values.get("VOICE_SAMPLE_RATE", "16000").strip() or "16000"
    tts_enabled_text = values.get("HERMES_TTS_ENABLED", "true").strip() or "true"
    wake_word = values.get("HERMES_WAKE_WORD", "hermes").strip() or "hermes"
    require_wake_word_text = (
        values.get("HERMES_REQUIRE_WAKE_WORD", "true").strip() or "true"
    )
    auto_voice_max_seconds_text = (
        values.get("HERMES_AUTO_VOICE_MAX_SECONDS", "8.0").strip() or "8.0"
    )
    auto_voice_silence_seconds_text = (
        values.get("HERMES_AUTO_VOICE_SILENCE_SECONDS", "1.2").strip() or "1.2"
    )
    auto_voice_silence_threshold_text = (
        values.get("HERMES_AUTO_VOICE_SILENCE_THRESHOLD", "0.012").strip() or "0.012"
    )

    missing = []
    if not bot_token:
        missing.append("DISCORD_BOT_TOKEN")
    if not channel_id_text:
        missing.append("DISCORD_CHANNEL_ID")

    if missing:
        raise ConfigError("Missing required setting(s): " + ", ".join(missing))

    channel_id = _parse_optional_int("DISCORD_CHANNEL_ID", channel_id_text)
    hermes_bot_id = (
        _parse_optional_int("DISCORD_APP_BOT_ID", hermes_bot_id_text)
        if hermes_bot_id_text
        else None
    )
    user_id = (
        _parse_optional_int("DISCORD_USER_ID", user_id_text) if user_id_text else None
    )
    voice_sample_rate = _parse_optional_int("VOICE_SAMPLE_RATE", voice_sample_rate_text)
    tts_enabled = _parse_bool("HERMES_TTS_ENABLED", tts_enabled_text)
    require_wake_word = _parse_bool("HERMES_REQUIRE_WAKE_WORD", require_wake_word_text)
    auto_voice_max_seconds = _parse_positive_float(
        "HERMES_AUTO_VOICE_MAX_SECONDS", auto_voice_max_seconds_text
    )
    auto_voice_silence_seconds = _parse_positive_float(
        "HERMES_AUTO_VOICE_SILENCE_SECONDS", auto_voice_silence_seconds_text
    )
    auto_voice_silence_threshold = _parse_positive_float(
        "HERMES_AUTO_VOICE_SILENCE_THRESHOLD", auto_voice_silence_threshold_text
    )

    return DiscordSettings(
        bot_token=bot_token,
        channel_id=channel_id,
        hermes_bot_id=hermes_bot_id,
        user_id=user_id,
        bot_token_source=bot_token_source,
        whisper_model_size=whisper_model_size,
        voice_sample_rate=voice_sample_rate,
        tts_enabled=tts_enabled,
        wake_word=wake_word.lower(),
        require_wake_word=require_wake_word,
        auto_voice_max_seconds=auto_voice_max_seconds,
        auto_voice_silence_seconds=auto_voice_silence_seconds,
        auto_voice_silence_threshold=auto_voice_silence_threshold,
    )


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ConfigError(f"Missing environment file: {path}")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = _strip_quotes(value.strip())

    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_optional_int(name: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be numeric") from exc


def _parse_bool(name: str, value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be true or false")


def _parse_positive_float(name: str, value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be numeric") from exc
    if parsed <= 0:
        raise ConfigError(f"{name} must be greater than 0")
    return parsed
