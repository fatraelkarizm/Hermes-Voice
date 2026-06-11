from __future__ import annotations

import asyncio
import re
from typing import Any

import discord
from PySide6.QtCore import QObject, Signal, Slot

from hermes_bridge.config import DiscordSettings


def format_user_command(
    command: str,
    user_id: int | None = None,
    hermes_bot_id: int | None = None,
) -> str:
    del user_id
    text = command.strip()
    if hermes_bot_id is None:
        return text
    return f"<@{hermes_bot_id}> {text}"


def bot_identity_warning(settings: DiscordSettings, connected_bot_id: int | None) -> str | None:
    if (
        settings.hermes_bot_id is not None
        and connected_bot_id is not None
        and settings.hermes_bot_id == connected_bot_id
    ):
        return (
            "Bridge token and DISCORD_APP_BOT_ID point to the same Discord bot. "
            "Discord will show the bridge message as that bot, and many agents ignore their own bot messages."
        )
    return None


def extract_reply_text(message: Any) -> str:
    parts: list[str] = []
    content = getattr(message, "content", "")
    if content and content.strip():
        parts.append(content.strip())

    for embed in getattr(message, "embeds", []) or []:
        description = getattr(embed, "description", "")
        if description and description.strip():
            parts.append(description.strip())
        for field in getattr(embed, "fields", []) or []:
            value = getattr(field, "value", "")
            if value and str(value).strip():
                parts.append(str(value).strip())

    return simplify_reply_text("\n".join(parts))


def simplify_reply_text(text: str) -> str:
    cleaned_lines = []
    for raw_line in text.replace("```", "\n").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered in {"terminal", "💻 terminal", "python", "bash", "powershell"}:
            continue
        if line.startswith("@"):
            continue
        if re.match(r"^(python|py|bash|pwsh|powershell)\b", lowered):
            continue
        cleaned_lines.append(line)

    if not cleaned_lines:
        return ""

    for line in reversed(cleaned_lines):
        if re.fullmatch(r"[-+]?\d+(\.\d+)?", line):
            return line
    return cleaned_lines[-1] if len(cleaned_lines) > 1 else cleaned_lines[0]


def should_accept_message(message: Any, hermes_bot_id: int | None) -> bool:
    if not extract_reply_text(message):
        return False

    author = getattr(message, "author", None)
    if author is None:
        return False

    if hermes_bot_id is not None:
        return getattr(author, "id", None) == hermes_bot_id

    return bool(getattr(author, "bot", False))


class DiscordBridgeWorker(QObject):
    system_event = Signal(str)
    status_changed = Signal(str)
    reply_received = Signal(str)
    command_sent = Signal(str)
    send_failed = Signal(str)

    def __init__(self, settings: DiscordSettings):
        super().__init__()
        self._settings = settings
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client: discord.Client | None = None
        self._channel: discord.abc.Messageable | None = None
        self._ready = asyncio.Event()
        self._reported_ignored_author_ids: set[int] = set()

    @Slot()
    def start(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ready = asyncio.Event()
        self._client = self._create_client()

        try:
            self._loop.run_until_complete(self._client.start(self._settings.bot_token))
        except Exception as exc:  # pragma: no cover - requires live Discord
            self.status_changed.emit("DISCONNECTED")
            self.system_event.emit(f"Discord connection failed: {exc}")
        finally:
            self._loop.run_until_complete(self._cleanup())
            self._loop.close()

    @Slot(str)
    def send_command(self, command: str) -> None:
        text = command.strip()
        if not text:
            return

        if self._loop is None or self._client is None:
            self.send_failed.emit("Discord worker is not running yet.")
            return

        asyncio.run_coroutine_threadsafe(self._send_message(text), self._loop)

    @Slot()
    def stop(self) -> None:
        if self._loop is None or self._client is None:
            return

        asyncio.run_coroutine_threadsafe(self._client.close(), self._loop)

    def _create_client(self) -> discord.Client:
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents)

        @client.event
        async def on_ready() -> None:
            self.status_changed.emit("ONLINE")
            self.system_event.emit(f"Discord connected as {client.user}")
            connected_bot_id = client.user.id if client.user is not None else None
            warning = bot_identity_warning(self._settings, connected_bot_id)
            if warning is not None:
                self.system_event.emit(warning)
            if self._settings.hermes_bot_id is not None:
                self.system_event.emit(
                    f"Listening for Hermes replies from bot ID {self._settings.hermes_bot_id}"
                )
                self.system_event.emit("Outgoing commands will mention Hermes because require_mention is enabled")
            else:
                self.system_event.emit("Listening for replies from any bot in the channel")
            self._channel = client.get_channel(self._settings.channel_id)
            if self._channel is None:
                self._channel = await client.fetch_channel(self._settings.channel_id)
            self._ready.set()

        @client.event
        async def on_message(message: discord.Message) -> None:
            if client.user is not None and message.author.id == client.user.id:
                return
            if message.channel.id != self._settings.channel_id:
                return
            if should_accept_message(message, self._settings.hermes_bot_id):
                self.reply_received.emit(extract_reply_text(message))
                return

            author_id = getattr(message.author, "id", None)
            if getattr(message.author, "bot", False) and author_id not in self._reported_ignored_author_ids:
                self._reported_ignored_author_ids.add(author_id)
                self.system_event.emit(
                    f"Ignored bot message from ID {author_id}; check DISCORD_APP_BOT_ID"
                )

        return client

    async def _send_message(self, command: str) -> None:
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=15)
            if self._channel is None:
                raise RuntimeError("Discord channel is not available.")
            await self._channel.send(
                format_user_command(
                    command,
                    user_id=self._settings.user_id,
                    hermes_bot_id=self._settings.hermes_bot_id,
                )
            )
            self.command_sent.emit(command)
        except Exception as exc:  # pragma: no cover - requires live Discord
            self.send_failed.emit(f"Failed to send command: {exc}")

    async def _cleanup(self) -> None:
        if self._client is not None and not self._client.is_closed():
            await self._client.close()
