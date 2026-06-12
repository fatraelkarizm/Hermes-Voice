from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from tempfile import gettempdir
from threading import Thread

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from hermes_bridge.config import ConfigError, load_settings
from hermes_bridge.desktop_actions import DesktopActionRunner
from hermes_bridge.discord_bridge import DiscordBridgeWorker
from hermes_bridge.single_instance import SingleInstanceLock
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


def greeting_delay_ms(message: str) -> int:
    words = max(1, len(message.split()))
    return min(3500, max(1200, words * 330))


def _voice_text_signature(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def is_self_echo_transcript(
    transcript: str,
    prompts: tuple[str, ...],
    max_extra_words: int = 6,
) -> bool:
    command_signature = _voice_text_signature(transcript)
    if not command_signature:
        return False

    command_words = command_signature.split()
    for prompt in prompts:
        prompt_signature = _voice_text_signature(prompt)
        if not prompt_signature:
            continue
        prompt_words = prompt_signature.split()
        if (
            prompt_signature in command_signature
            and len(command_words) <= len(prompt_words) + max_extra_words
        ):
            return True
    return False


def is_spurious_auto_transcript(transcript: str) -> bool:
    normalized = _voice_text_signature(transcript)
    if not normalized:
        return True
    if normalized in {
        "you",
        "hi",
        "hello",
        "thank you",
        "thank you for watching",
        "thanks for watching",
        "bye",
        "bye bye",
    }:
        return True
    return False


def is_voice_stop_command(command: str, wake_phrases: tuple[str, ...]) -> bool:
    stripped = strip_wake_phrase(command, wake_phrases)
    normalized = _voice_text_signature(stripped if stripped is not None else command)
    if normalized in {
        "stop",
        "stopped",
        "stop listening",
        "stop voice",
        "voice stop",
        "turn off voice",
        "matikan voice",
        "matikan suara",
        "berhenti",
        "berhenti dulu",
    }:
        return True

    words = normalized.split()
    if len(words) <= 4 and words[-1:] in (["stop"], ["stopped"]):
        return normalized not in {"dont stop", "don t stop", "do not stop"}

    return any(
        phrase in normalized
        for phrase in ("stop listening", "stop voice", "turn off voice")
    )


def is_app_shutdown_command(command: str, wake_phrases: tuple[str, ...]) -> bool:
    stripped = strip_wake_phrase(command, wake_phrases)
    normalized = _voice_text_signature(stripped if stripped is not None else command)
    return normalized in {
        "shutdown",
        "shutdown app",
        "shut down",
        "shut down app",
        "quit",
        "quit app",
        "quit hermes",
        "exit",
        "exit app",
        "exit hermes",
        "close app",
        "close this app",
        "close hermes",
        "matikan app",
        "matikan hermes",
    }


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
    instance_lock = SingleInstanceLock(Path(gettempdir()) / "hermes-voice.lock")
    if not instance_lock.acquire():
        write_log("SYS: Another Hermes Voice instance is already running. Exiting.")
        return 0

    app = QApplication([sys.argv[0]])
    app.aboutToQuit.connect(instance_lock.release)
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
    voice_generation = 0

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
        desktop_actions = DesktopActionRunner()

        def bump_voice_generation() -> int:
            nonlocal voice_generation
            voice_generation += 1
            return voice_generation

        def stop_voice_capture() -> None:
            if wake_listener is not None:
                wake_listener.stop_listening()
            if voice_worker is not None:
                voice_worker.cancel_recording()

        def disable_voice_mode(message: str) -> None:
            nonlocal voice_mode_enabled, wake_word_armed, waiting_for_hermes_reply
            bump_voice_generation()
            voice_mode_enabled = False
            wake_word_armed = False
            waiting_for_hermes_reply = False
            stop_voice_capture()
            window.stop_speech()
            window.set_voice_mode_enabled(False)
            window.set_voice_ready()
            append_system(message)

        def shutdown_app(message: str) -> None:
            nonlocal voice_mode_enabled, wake_word_armed, waiting_for_hermes_reply
            bump_voice_generation()
            voice_mode_enabled = False
            wake_word_armed = False
            waiting_for_hermes_reply = False
            stop_voice_capture()
            window.stop_speech()
            worker_ref = worker
            if worker_ref is not None:
                worker_ref.stop()
            append_system(message)
            app.quit()

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
            generation = voice_generation

            def rearm_if_current() -> None:
                if (
                    generation != voice_generation
                    or not voice_mode_enabled
                    or waiting_for_hermes_reply
                ):
                    return
                if wake_listener is not None and settings.require_wake_word:
                    start_wake_listening(0)
                    return
                start_auto_voice(0)

            QTimer.singleShot(delay_ms, rearm_if_current)

        def greet_after_wake() -> None:
            greeting = settings.wake_greeting
            bump_voice_generation()
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

        def handle_reply_timeout() -> None:
            nonlocal waiting_for_hermes_reply
            if not waiting_for_hermes_reply:
                return
            waiting_for_hermes_reply = False
            append_system("SYS: Hermes reply timeout. Re-arming wake word.")
            if voice_mode_enabled:
                rearm_voice_mode()

        def handle_voice_mode_toggle(enabled: bool) -> None:
            nonlocal voice_mode_enabled, wake_word_armed
            bump_voice_generation()
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

            if is_app_shutdown_command(command, settings.wake_word_aliases):
                shutdown_app("SYS: Hermes Voice shutdown by voice command.")
                return

            prompts = (settings.wake_greeting, settings.follow_up_prompt)
            if is_self_echo_transcript(command, prompts):
                append_system(f"SYS: Ignored Hermes self-echo transcript: {command}")
                window.set_voice_ready()
                rearm_voice_mode(1500)
                return

            if is_voice_stop_command(command, settings.wake_word_aliases):
                disable_voice_mode("SYS: Voice mode stopped by voice command.")
                return

            if voice_mode_enabled and is_spurious_auto_transcript(command):
                append_system(f"SYS: Ignored low-confidence voice transcript: {command}")
                window.set_voice_ready()
                rearm_voice_mode(1500)
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
            QTimer.singleShot(
                int(settings.reply_timeout_seconds * 1000),
                handle_reply_timeout,
            )

        def handle_hermes_reply(message: str) -> None:
            nonlocal waiting_for_hermes_reply
            stop_voice_capture()
            generation = bump_voice_generation()
            write_log(f"HERMES: {message}")
            window.append_hermes_reply(message)
            reply_action = desktop_actions.run_reply(message)
            if reply_action.handled:
                append_system(f"SYS: Agent local action: {reply_action.message}")
            waiting_for_hermes_reply = False
            if voice_mode_enabled:
                speak_delay_ms = min(9000, max(1800, max(1, len(message.split())) * 330))
                if settings.follow_up_enabled and settings.follow_up_prompt:
                    def speak_follow_up() -> None:
                        if generation != voice_generation or not voice_mode_enabled:
                            return
                        window.append_hermes_reply(settings.follow_up_prompt)
                        write_log(f"HERMES: {settings.follow_up_prompt}")
                        rearm_voice_mode(greeting_delay_ms(settings.follow_up_prompt))

                    QTimer.singleShot(speak_delay_ms, speak_follow_up)
                else:
                    rearm_voice_mode(speak_delay_ms)

        def handle_command_submitted(command: str) -> None:
            if is_app_shutdown_command(command, settings.wake_word_aliases):
                shutdown_app("SYS: Hermes Voice shutdown by command.")
                return

            if is_voice_stop_command(command, settings.wake_word_aliases):
                disable_voice_mode("SYS: Voice mode stopped by command.")
                return

            bump_voice_generation()
            result = desktop_actions.run(command)
            if result.handled:
                append_system(f"SYS: Local action: {result.message}")
                window.append_hermes_reply(result.message)
                write_log(f"HERMES: {result.message}")
                if voice_mode_enabled:
                    if settings.follow_up_enabled and settings.follow_up_prompt:
                        def speak_local_follow_up() -> None:
                            if not voice_mode_enabled:
                                return
                            window.append_hermes_reply(settings.follow_up_prompt)
                            write_log(f"HERMES: {settings.follow_up_prompt}")
                            rearm_voice_mode(greeting_delay_ms(settings.follow_up_prompt))

                        QTimer.singleShot(
                            greeting_delay_ms(result.message), speak_local_follow_up
                        )
                    else:
                        rearm_voice_mode(greeting_delay_ms(result.message))
                return
            worker_ref = worker
            if worker_ref is not None:
                worker_ref.send_command(command)

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
        window.voice_stop_requested.connect(
            lambda: disable_voice_mode("SYS: Voice mode stopped by button.")
        )
        window.app_shutdown_requested.connect(
            lambda: shutdown_app("SYS: Hermes Voice shutdown by button.")
        )
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
        window.command_submitted.connect(handle_command_submitted)
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
