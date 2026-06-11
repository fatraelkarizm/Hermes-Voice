# Hermes Voice

Hermes Voice is a desktop companion app for controlling a Hermes Discord agent with voice. It provides a custom PySide6 interface, local speech-to-text through `faster-whisper`, Discord bridge messaging, and text-to-speech replies.

The app can run in the background on Windows and only show itself when the wake word is detected, for example: `Hermes, what can you do?`

## Features

- Futuristic desktop UI built with PySide6
- Push-to-talk voice input
- Hands-free voice mode with wake word support
- Local speech-to-text using `faster-whisper`
- Discord bridge for sending commands to a Hermes bot/agent
- Conversation log for user commands and Hermes replies
- Text-to-speech playback for Hermes replies
- Optional Windows startup launcher
- Hidden startup mode: listen in the background, then show the UI when you say `Hermes`

## Requirements

- Windows
- Python 3.11+
- A Discord bot token for the bridge account
- A Discord channel ID where Hermes listens/responds
- Optional: Hermes agent bot ID, used to mention and filter replies

Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configuration

Create a local `.env` file in the project root. Do not commit this file.

```env
DISCORD_BOT_TOKEN=your_bridge_bot_token
DISCORD_CHANNEL_ID=your_channel_id
DISCORD_APP_BOT_ID=your_hermes_agent_bot_id

WHISPER_MODEL_SIZE=tiny
VOICE_SAMPLE_RATE=16000

HERMES_TTS_ENABLED=true
HERMES_WAKE_WORD=hermes
HERMES_REQUIRE_WAKE_WORD=true
HERMES_AUTO_VOICE_MAX_SECONDS=8.0
HERMES_AUTO_VOICE_SILENCE_SECONDS=1.2
HERMES_AUTO_VOICE_SILENCE_THRESHOLD=0.012
```

### Discord token note

The bridge token should ideally belong to a different Discord bot/account than the Hermes agent bot. If the bridge sends messages as the same bot that should answer, the Hermes agent may ignore its own messages.

## Run the app

Normal desktop mode:

```bash
.venv\Scripts\python.exe app.py
```

Start with hands-free voice mode enabled:

```bash
.venv\Scripts\python.exe app.py --voice-mode
```

Start hidden in the background until the wake word is detected:

```bash
.venv\Scripts\python.exe app.py --start-hidden --voice-mode
```

In hidden voice mode, the app process is running, but the window is not shown. Say the wake word, such as `Hermes`, and the UI will appear.

## Voice modes

### Push-to-talk

Use the `HOLD TO TALK` button in the UI. Hold while speaking, then release to transcribe and send the command.

### Hands-free voice mode

Enable `VOICE MODE` in the UI or launch with `--voice-mode`.

With the default config, Hermes only reacts when the wake word is included:

```text
Hermes, summarize my schedule
Hermes, what is the weather today?
```

If only the wake word is detected, the app wakes up and starts listening for the next command.

## Windows startup

Install the startup launcher:

```bash
.venv\Scripts\python.exe tools\install_windows_startup.py
```

This creates a `Hermes Voice.bat` file in the current user's Windows Startup folder:

```text
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

You can open that folder manually with:

```text
Win + R -> shell:startup
```

After installation, Hermes starts automatically after Windows login in hidden voice mode. The UI will not appear immediately; it listens in the background and appears when you say the wake word.

Remove the startup launcher:

```bash
.venv\Scripts\python.exe tools\uninstall_windows_startup.py
```

Or delete `Hermes Voice.bat` manually from `shell:startup`.

## Tests

Run the test suite:

```bash
.venv\Scripts\python.exe -m pytest
```

## Project structure

```text
app.py                         # Application entrypoint
hermes_bridge/config.py         # Environment/config loading
hermes_bridge/discord_bridge.py # Discord bridge worker
hermes_bridge/ui/               # PySide6 UI
hermes_bridge/voice/            # Audio recording and Whisper transcription
tools/                          # Windows startup install/uninstall helpers
tests/                          # Unit tests
```

## Security

`.env`, `.env.*`, `.venv`, and Python cache files are ignored by Git. Never commit Discord bot tokens or other secrets.
