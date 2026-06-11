from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from threading import Thread

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from hermes_bridge.config import ConfigError, load_settings
from hermes_bridge.discord_bridge import DiscordBridgeWorker
from hermes_bridge.ui.main_window import HermesMainWindow
from hermes_bridge.ui.styles import APP_STYLE
from hermes_bridge.voice.input_worker import VoiceInputWorker


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hermes Voice Bridge")
    parser.add_argument(
        "--start-minimized",
        action="store_true",
        help="Start Hermes minimized.",
    )
    parser.add_argument(
        "--start-hidden",
        action="store_true",
        help="Start Hermes in the background until the wake word is detected.",
    )
    parser.add_argument(
        "--voice-mode",
        action="store_true",
        help="Enable hands-free voice mode at launch.",
    )
    return parser.parse_args(argv)


WAKE_WORD_ALIASES = (
    "hermes",
    "ermes",
    "hermis",
    "hermies",
    "her mess",
    "her miss",
    "hey hermes",
    "hey ermes",
    "harness",
    "herman",
    "her man",
    "harm us",
)


def strip_wake_word(command: str, wake_word: str) -> str | None:
    lowered = command.lower()
    aliases = sorted({wake_word.lower(), *WAKE_WORD_ALIASES}, key=len, reverse=True)
    for alias in aliases:
        pattern = rf"\b{re.escape(alias)}\b"
        match = re.search(pattern, lowered)
        if match is None:
            continue
        stripped = command[: match.start()] + command[match.end() :]
        return " ".join(stripped.strip(" ,.!?:;-\t\n").split())
    return None


LOG_PATH = Path("hermes-voice.log")


def write_log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except OSError:
        pass


def main() -> int:
    args = parse_args(sys.argv[1:])
    write_log(f"Starting Hermes Voice with args: {sys.argv[1:]}")
    app = QApplication([sys.argv[0]])
    if args.start_hidden:
        app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(APP_STYLE)

    window = HermesMainWindow()

    def append_system(message: str) -> None:
        write_log(message)
        window.append_system(message)

    append_system("SYS: Hermes module initialized.")
    voice_worker: VoiceInputWorker | None = None
    voice_mode_enabled = False
    wake_word_armed = args.voice_mode
    waiting_for_hermes_reply = False

    worker_thread: Thread | None = None
    worker: DiscordBridgeWorker | None = None

    try:
        settings = load_settings(".env")
    except ConfigError as exc:
        window.set_status("CONFIG REQUIRED")
        window.set_voice_disabled()
        append_system(f"SYS: {exc}")
        append_system("SYS: Fill .env, then restart the bridge.")
    else:
        window.set_tts_enabled(settings.tts_enabled)

        def start_auto_voice(delay_ms: int = 250) -> None:
            worker_ref = voice_worker
            if worker_ref is None or not voice_mode_enabled:
                return

            def start_if_still_enabled() -> None:
                if not voice_mode_enabled:
                    return
                worker_ref.start_auto_recording(
                    max_seconds=settings.auto_voice_max_seconds,
                    silence_seconds=settings.auto_voice_silence_seconds,
                    silence_threshold=settings.auto_voice_silence_threshold,
                )

            QTimer.singleShot(delay_ms, start_if_still_enabled)

        def handle_voice_mode_toggle(enabled: bool) -> None:
            nonlocal voice_mode_enabled, wake_word_armed
            voice_mode_enabled = enabled
            wake_word_armed = enabled and settings.require_wake_word
            window.set_voice_mode_enabled(enabled)
            if enabled:
                append_system(
                    f"SYS: Say '{settings.wake_word}' to wake Hermes."
                    if settings.require_wake_word
                    else "SYS: Voice mode will send detected speech automatically."
                )
                start_auto_voice()
            elif voice_worker is not None:
                voice_worker.stop_recording()

        def handle_voice_transcript(transcript: str) -> None:
            nonlocal wake_word_armed, waiting_for_hermes_reply
            command = transcript.strip()
            if not command:
                window.set_voice_ready()
                start_auto_voice(750)
                return

            if voice_mode_enabled and wake_word_armed:
                stripped = strip_wake_word(command, settings.wake_word)
                if stripped is None:
                    append_system(f"SYS: Ignored voice without wake word: {command}")
                    window.set_voice_ready()
                    start_auto_voice(750)
                    return

                window.show_activated()
                wake_word_armed = False
                command = stripped
                if not command:
                    append_system("SYS: Wake word detected. Listening for command.")
                    window.set_voice_ready()
                    start_auto_voice(350)
                    return

            append_system(f"SYS: Accepted voice transcript: {command}")
            waiting_for_hermes_reply = True
            window.submit_voice_transcript(command)
            window.set_voice_ready()

        def handle_hermes_reply(message: str) -> None:
            nonlocal waiting_for_hermes_reply
            write_log(f"HERMES: {message}")
            window.append_hermes_reply(message)
            waiting_for_hermes_reply = False
            if voice_mode_enabled:
                words = max(1, len(message.split()))
                speak_delay_ms = min(9000, max(1800, words * 330))
                start_auto_voice(speak_delay_ms)

        def handle_voice_error(message: str) -> None:
            write_log(f"SYS: {message}")
            window.set_voice_error(message)
            start_auto_voice(1000)

        voice_worker = VoiceInputWorker(
            sample_rate=settings.voice_sample_rate,
            model_size=settings.whisper_model_size,
        )
        window.voice_pressed.connect(window.set_voice_listening)
        voice_worker.recording_started.connect(
            lambda: append_system("SYS: Voice recording started.")
        )
        voice_worker.recording_started.connect(window.set_voice_listening)
        voice_worker.transcribing_started.connect(
            lambda: append_system("SYS: Transcribing voice command.")
        )
        voice_worker.transcribing_started.connect(window.set_voice_transcribing)
        voice_worker.transcript_ready.connect(handle_voice_transcript)
        voice_worker.voice_error.connect(handle_voice_error)
        window.voice_pressed.connect(voice_worker.start_recording)
        window.voice_released.connect(voice_worker.stop_recording)
        window.voice_mode_toggled.connect(handle_voice_mode_toggle)
        app.aboutToQuit.connect(voice_worker.stop_recording)
        append_system(
            f"SYS: Push-to-talk voice ready with faster-whisper '{settings.whisper_model_size}'."
        )
        if settings.tts_enabled:
            append_system("SYS: Hermes text-to-speech replies enabled.")
        else:
            append_system("SYS: Hermes text-to-speech replies disabled.")
        window.set_status("CONNECTING")
        append_system(f"SYS: Bridge login token source: {settings.bot_token_source}")
        worker = DiscordBridgeWorker(settings)
        worker_thread = Thread(target=worker.start, name="DiscordBridge", daemon=True)

        worker.status_changed.connect(window.set_status)
        worker.system_event.connect(append_system)
        worker.reply_received.connect(handle_hermes_reply)
        worker.send_failed.connect(window.keep_command_for_retry)
        worker.command_sent.connect(
            lambda command: append_system(f"SYS: Sent command: {command}")
        )
        worker.command_sent.connect(
            lambda _command: append_system(
                "SYS: Waiting for Hermes reply. If nothing appears, the Hermes bot is likely ignoring bot-authored messages."
            )
        )
        window.command_submitted.connect(worker.send_command)
        app.aboutToQuit.connect(worker.stop)

        worker_thread.start()

        if args.voice_mode:
            QTimer.singleShot(1000, lambda: handle_voice_mode_toggle(True))

    if args.start_hidden:
        write_log("SYS: Window hidden until wake word is detected.")
    elif args.start_minimized:
        window.showMinimized()
    else:
        window.show()
    exit_code = app.exec()

    if worker_thread is not None:
        worker_thread.join(timeout=3)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
