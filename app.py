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
from hermes_bridge.voice.wake_word import OpenWakeWordListener


LOG_PATH = Path("hermes-voice.log")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hermes Voice Bridge")
    parser.add_argument(
        "--start-minimized",
        action="store_true",
        help="Start Hermes minimized, useful for Windows startup.",
    )
    parser.add_argument(
        "--start-hidden",
        action="store_true",
        help="Start Hermes hidden until the wake word is detected.",
    )
    parser.add_argument(
        "--voice-mode",
        action="store_true",
        help="Enable hands-free voice mode at launch.",
    )
    return parser.parse_args(argv)


def format_log_line(message: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {message}"


def write_log(message: str) -> None:
    try:
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(format_log_line(message) + "\n")
    except OSError:
        pass


def strip_wake_word(command: str, wake_word: str) -> str | None:
    pattern = rf"\b{re.escape(wake_word.lower())}\b"
    match = re.search(pattern, command.lower())
    if match is None:
        return None
    stripped = command[: match.start()] + command[match.end() :]
    return " ".join(stripped.strip(" ,.!?:;-\t\n").split())


def strip_wake_phrase(command: str, wake_phrases: tuple[str, ...]) -> str | None:
    for phrase in sorted(wake_phrases, key=len, reverse=True):
        pattern = rf"\b{re.escape(phrase.lower())}\b"
        match = re.search(pattern, command.lower())
        if match is None:
            continue
        stripped = command[: match.start()] + command[match.end() :]
        return " ".join(stripped.strip(" ,.!?:;-\t\n").split())
    return None


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
    wake_listener: OpenWakeWordListener | None = None
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

        def start_wake_listening(delay_ms: int = 250) -> None:
            listener_ref = wake_listener
            if listener_ref is None or not voice_mode_enabled:
                return

            def start_if_still_enabled() -> None:
                if voice_mode_enabled and not waiting_for_hermes_reply:
                    listener_ref.start_listening()

            QTimer.singleShot(delay_ms, start_if_still_enabled)

        def rearm_voice_mode(delay_ms: int = 750) -> None:
            if wake_listener is not None and settings.require_wake_word:
                start_wake_listening(delay_ms)
                return
            start_auto_voice(delay_ms)

        def greeting_delay_ms(message: str) -> int:
            words = max(1, len(message.split()))
            return min(3000, max(1000, words * 260))

        def greet_after_wake() -> None:
            greeting = settings.wake_greeting
            if greeting:
                window.append_hermes_reply(greeting)
                write_log(f"HERMES: {greeting}")
            start_auto_voice(greeting_delay_ms(greeting))

        def handle_openwakeword_detected(model_name: str, score: float) -> None:
            nonlocal wake_word_armed
            wake_word_armed = False
            window.show_activated()
            append_system(
                f"SYS: Wake word detected by openWakeWord ({model_name}, {score:.2f})."
            )
            greet_after_wake()

        def handle_voice_mode_toggle(enabled: bool) -> None:
            nonlocal voice_mode_enabled, wake_word_armed
            voice_mode_enabled = enabled
            wake_word_armed = enabled and settings.require_wake_word
            window.set_voice_mode_enabled(enabled)
            if enabled:
                append_system(
                    f"SYS: Say '{' or '.join(settings.wake_word_aliases)}' to wake Hermes."
                    if settings.require_wake_word
                    else "SYS: Voice mode will send detected speech automatically."
                )
                if wake_listener is not None and settings.require_wake_word:
                    start_wake_listening()
                else:
                    start_auto_voice()
            else:
                if wake_listener is not None:
                    wake_listener.stop_listening()
                if voice_worker is not None:
                    voice_worker.stop_recording()

        def handle_voice_transcript(transcript: str) -> None:
            nonlocal wake_word_armed, waiting_for_hermes_reply
            command = transcript.strip()
            if not command:
                window.set_voice_ready()
                rearm_voice_mode(750)
                return

            if voice_mode_enabled and wake_word_armed and wake_listener is None:
                stripped = strip_wake_phrase(command, settings.wake_word_aliases)
                if stripped is None:
                    append_system(
                        f"SYS: Ignored voice without wake word: {command}"
                    )
                    window.set_voice_ready()
                    rearm_voice_mode(750)
                    return

                window.show_activated()
                wake_word_armed = False
                command = stripped
                greet_after_wake()
                if not command:
                    append_system(
                        "SYS: Wake word detected. Listening for command."
                    )
                    window.set_voice_ready()
                    return

            waiting_for_hermes_reply = True
            window.submit_voice_transcript(command)
            window.set_voice_ready()
            wake_word_armed = voice_mode_enabled and settings.require_wake_word

        def handle_hermes_reply(message: str) -> None:
            nonlocal waiting_for_hermes_reply
            write_log(f"HERMES: {message}")
            window.append_hermes_reply(message)
            waiting_for_hermes_reply = False
            if voice_mode_enabled:
                words = max(1, len(message.split()))
                speak_delay_ms = min(9000, max(1800, words * 330))
                rearm_voice_mode(speak_delay_ms)

        voice_worker = VoiceInputWorker(
            sample_rate=settings.voice_sample_rate,
            model_size=settings.whisper_model_size,
        )
        openwakeword_models = tuple(
            str(Path(path))
            for path in settings.openwakeword_model_paths
            if Path(path).exists()
        )
        if settings.require_wake_word and settings.wake_backend in {
            "hybrid",
            "openwakeword",
        }:
            if openwakeword_models:
                wake_listener = OpenWakeWordListener(
                    model_paths=openwakeword_models,
                    aliases=settings.wake_word_aliases,
                    sample_rate=settings.voice_sample_rate,
                    threshold=settings.openwakeword_threshold,
                    debounce_seconds=settings.openwakeword_debounce_seconds,
                    chunk_size=settings.openwakeword_chunk_size,
                    inference_framework=settings.openwakeword_inference_framework,
                )
                wake_listener.wake_listening.connect(
                    lambda: append_system("SYS: openWakeWord listening.")
                )
                wake_listener.wake_detected.connect(handle_openwakeword_detected)
                wake_listener.wake_error.connect(window.set_voice_error)
                wake_listener.wake_error.connect(lambda message: write_log(f"SYS: {message}"))
                wake_listener.wake_error.connect(lambda _message: rearm_voice_mode(1000))
                app.aboutToQuit.connect(wake_listener.stop_listening)
            elif settings.wake_backend == "openwakeword":
                append_system(
                    "SYS: openWakeWord requested, but no configured model files exist."
                )
            else:
                append_system(
                    "SYS: No openWakeWord model found; using Whisper wake phrase fallback."
                )
        window.voice_pressed.connect(window.set_voice_listening)
        if wake_listener is not None:
            window.voice_pressed.connect(wake_listener.stop_listening)
        voice_worker.recording_started.connect(
            lambda: append_system("SYS: Voice recording started.")
        )
        voice_worker.recording_started.connect(window.set_voice_listening)
        voice_worker.transcribing_started.connect(
            lambda: append_system("SYS: Transcribing voice command.")
        )
        voice_worker.transcribing_started.connect(window.set_voice_transcribing)
        voice_worker.transcript_ready.connect(handle_voice_transcript)
        voice_worker.voice_error.connect(window.set_voice_error)
        voice_worker.voice_error.connect(lambda message: write_log(f"SYS: {message}"))
        voice_worker.voice_error.connect(lambda _message: rearm_voice_mode(1000))
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
        append_system(
            f"SYS: Bridge login token source: {settings.bot_token_source}"
        )
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
        window.hide()
        append_system("SYS: Window hidden until wake word is detected.")
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
