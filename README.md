# Hermes Voice

Hermes Voice is a Windows desktop companion for talking to Hermes through a Discord bridge.
It supports push-to-talk, hidden startup, text-to-speech replies, and a local wake-word flow using openWakeWord.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools\setup_wakeword.py
```

Create `.env` from `.env.example`, then fill your Discord values:

```text
DISCORD_BOT_TOKEN=
DISCORD_BOT_TOKEN_V2=
DISCORD_CHANNEL_ID=
DISCORD_APP_BOT_ID=
DISCORD_USER_ID=
```

Keep `.env` private. It is ignored by git.

## Run

Visible voice mode:

```powershell
.\.venv\Scripts\python.exe app.py --voice-mode
```

Hidden wake-word mode:

```powershell
.\.venv\Scripts\python.exe tools\start_hermes_hidden.py
```

Say:

```text
Hey Hermes
```

When the wake word triggers, the window shows and Hermes says:

```text
Hi, What Can I Help You?
```

## Windows Startup

Install hidden startup:

```powershell
.\.venv\Scripts\python.exe tools\install_windows_startup.py
```

Remove startup:

```powershell
.\.venv\Scripts\python.exe tools\uninstall_windows_startup.py
```

## Wake Word

The app uses `HERMES_WAKE_BACKEND=hybrid`.
If the downloaded openWakeWord model exists, it listens locally for "Hey Hermes".
If the model is missing, it falls back to Whisper phrase detection.

The local model path is:

```text
models/hey_hermes/hey_hermes_cnn_v1.onnx
```

Wake-word model binaries are ignored by git. Reinstall them with:

```powershell
.\.venv\Scripts\python.exe tools\setup_wakeword.py
```

## Local Desktop Actions

Some commands are handled locally before they go to Discord:

```text
open youtube
buka google
open github
open chatgpt
open chrome
open discord
open vscode
open spotify
open notepad
open calculator
```

These actions use a safe-list. Unknown desktop commands are sent to Hermes through Discord instead.

## Troubleshooting

Logs are written to:

```text
hermes-voice.log
```

If "Hey Hermes" does not wake the app:

1. Run `tools\setup_wakeword.py` again.
2. Restart with `tools\start_hermes_hidden.py`.
3. Check `hermes-voice.log` for `openWakeWord listening` or wake-word errors.
4. Lower `HERMES_OPENWAKEWORD_THRESHOLD` in `.env` if your mic is quiet.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
