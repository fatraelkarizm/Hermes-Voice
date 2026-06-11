from types import SimpleNamespace

from hermes_bridge.config import DiscordSettings
from hermes_bridge.discord_bridge import (
    bot_identity_warning,
    extract_reply_text,
    format_user_command,
    should_accept_message,
)


def message(author_id: int, content: str = "hello", bot: bool = True, embeds=None):
    return SimpleNamespace(
        author=SimpleNamespace(id=author_id, bot=bot),
        content=content,
        embeds=embeds or [],
    )


def test_format_user_command_sends_plain_user_text():
    assert format_user_command(" buka chrome ") == "buka chrome"


def test_format_user_command_ignores_user_id_for_discord_payload():
    assert format_user_command("apa 200 x 200", user_id=555555555) == "apa 200 x 200"


def test_format_user_command_mentions_hermes_bot_when_configured():
    assert (
        format_user_command("200 x 200", hermes_bot_id=987654321)
        == "<@987654321> 200 x 200"
    )


def test_should_accept_message_accepts_configured_hermes_bot():
    incoming = message(author_id=987654321, content="Siap bre.")

    assert should_accept_message(incoming, hermes_bot_id=987654321) is True


def test_should_accept_message_rejects_other_bots_when_hermes_id_is_configured():
    incoming = message(author_id=111111111, content="noise")

    assert should_accept_message(incoming, hermes_bot_id=987654321) is False


def test_should_accept_message_without_hermes_id_accepts_bot_messages_only():
    assert should_accept_message(message(author_id=1, bot=True), hermes_bot_id=None) is True
    assert should_accept_message(message(author_id=2, bot=False), hermes_bot_id=None) is False


def test_should_accept_message_rejects_empty_content():
    incoming = message(author_id=987654321, content="   ")

    assert should_accept_message(incoming, hermes_bot_id=987654321) is False


def test_extract_reply_text_prefers_final_terminal_output():
    incoming = message(
        author_id=987654321,
        content="@Agentic This is 2 times 2.\n💻 terminal\npython - <<'PY' ...\n4",
    )

    assert extract_reply_text(incoming) == "4"


def test_extract_reply_text_reads_embed_fields_when_content_is_empty():
    embed = SimpleNamespace(
        title="terminal",
        description="python - <<'PY' ...",
        fields=[SimpleNamespace(name="output", value="4")],
    )
    incoming = message(author_id=987654321, content="", embeds=[embed])

    assert extract_reply_text(incoming) == "4"


def test_should_accept_message_accepts_configured_bot_with_embed_reply():
    embed = SimpleNamespace(title="result", description="4", fields=[])
    incoming = message(author_id=987654321, content="", embeds=[embed])

    assert should_accept_message(incoming, hermes_bot_id=987654321) is True


def test_bot_identity_warning_detects_same_bridge_and_hermes_bot():
    settings = DiscordSettings(
        bot_token="secret",
        channel_id=123,
        hermes_bot_id=987654321,
    )

    warning = bot_identity_warning(settings, connected_bot_id=987654321)

    assert warning is not None
    assert "same Discord bot" in warning


def test_bot_identity_warning_allows_different_bridge_and_hermes_bots():
    settings = DiscordSettings(
        bot_token="secret",
        channel_id=123,
        hermes_bot_id=987654321,
    )

    assert bot_identity_warning(settings, connected_bot_id=111111111) is None
