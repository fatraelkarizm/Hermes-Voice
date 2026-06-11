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
    wake_word_aliases: tuple[str, ...] = ("hey hermes", "hermes")
    require_wake_word: bool = True
    wake_backend: str = "hybrid"
    openwakeword_model_paths: tuple[str, ...] = ()
    openwakeword_threshold: float = 0.35
    openwakeword_debounce_seconds: float = 2.0
    openwakeword_chunk_size: int = 1280
    openwakeword_inference_framework: str = "onnx"
    wake_greeting: str = "Hi, What Can I Help You?"
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
    wake_word_aliases_text = values.get("HERMES_WAKE_WORD_ALIASES", "").strip()
    require_wake_word_text = (
        values.get("HERMES_REQUIRE_WAKE_WORD", "true").strip() or "true"
    )
    wake_backend = values.get("HERMES_WAKE_BACKEND", "hybrid").strip() or "hybrid"
    openwakeword_models_text = values.get("HERMES_OPENWAKEWORD_MODELS", "").strip()
    openwakeword_threshold_text = (
        values.get("HERMES_OPENWAKEWORD_THRESHOLD", "0.35").strip() or "0.35"
    )
    openwakeword_debounce_text = (
        values.get("HERMES_OPENWAKEWORD_DEBOUNCE_SECONDS", "2.0").strip() or "2.0"
    )
    openwakeword_chunk_size_text = (
        values.get("HERMES_OPENWAKEWORD_CHUNK_SIZE", "1280").strip() or "1280"
    )
    openwakeword_inference_framework = (
        values.get("HERMES_OPENWAKEWORD_INFERENCE_FRAMEWORK", "onnx").strip() or "onnx"
    )
    wake_greeting = (
        values.get("HERMES_WAKE_GREETING", "Hi, What Can I Help You?").strip()
        or "Hi, What Can I Help You?"
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
    wake_word_aliases = _parse_wake_aliases(wake_word_aliases_text, wake_word)
    require_wake_word = _parse_bool("HERMES_REQUIRE_WAKE_WORD", require_wake_word_text)
    wake_backend = _parse_choice(
        "HERMES_WAKE_BACKEND", wake_backend.lower(), {"hybrid", "whisper", "openwakeword"}
    )
    openwakeword_model_paths = _parse_path_list(openwakeword_models_text)
    openwakeword_threshold = _parse_threshold(
        "HERMES_OPENWAKEWORD_THRESHOLD", openwakeword_threshold_text
    )
    openwakeword_debounce_seconds = _parse_positive_float(
        "HERMES_OPENWAKEWORD_DEBOUNCE_SECONDS", openwakeword_debounce_text
    )
    openwakeword_chunk_size = _parse_optional_int(
        "HERMES_OPENWAKEWORD_CHUNK_SIZE", openwakeword_chunk_size_text
    )
    if openwakeword_chunk_size <= 0:
        raise ConfigError("HERMES_OPENWAKEWORD_CHUNK_SIZE must be greater than 0")
    openwakeword_inference_framework = _parse_choice(
        "HERMES_OPENWAKEWORD_INFERENCE_FRAMEWORK",
        openwakeword_inference_framework.lower(),
        {"onnx", "tflite"},
    )
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
        wake_word_aliases=wake_word_aliases,
        require_wake_word=require_wake_word,
        wake_backend=wake_backend,
        openwakeword_model_paths=openwakeword_model_paths,
        openwakeword_threshold=openwakeword_threshold,
        openwakeword_debounce_seconds=openwakeword_debounce_seconds,
        openwakeword_chunk_size=openwakeword_chunk_size,
        openwakeword_inference_framework=openwakeword_inference_framework,
        wake_greeting=wake_greeting,
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


def _parse_choice(name: str, value: str, choices: set[str]) -> str:
    if value in choices:
        return value
    raise ConfigError(f"{name} must be one of: {', '.join(sorted(choices))}")


def _parse_path_list(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    normalized = value.replace(",", ";")
    return tuple(part.strip() for part in normalized.split(";") if part.strip())


def _parse_wake_aliases(value: str, wake_word: str) -> tuple[str, ...]:
    aliases = [part.lower() for part in _parse_path_list(value)]
    if not aliases:
        aliases = [f"hey {wake_word.lower()}", wake_word.lower()]
    unique_aliases = []
    for alias in aliases:
        normalized = " ".join(alias.split())
        if normalized and normalized not in unique_aliases:
            unique_aliases.append(normalized)
    return tuple(sorted(unique_aliases, key=len, reverse=True))


def _parse_threshold(name: str, value: str) -> float:
    parsed = _parse_positive_float(name, value)
    if parsed > 1:
        raise ConfigError(f"{name} must be between 0 and 1")
    return parsed


def _parse_positive_float(name: str, value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be numeric") from exc
    if parsed <= 0:
        raise ConfigError(f"{name} must be greater than 0")
    return parsed
