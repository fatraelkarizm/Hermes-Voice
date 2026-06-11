# Hermes Desktop GUI Bridge Design

## Goal

Build a lightweight Windows desktop companion app for Hermes Desktop. The app should feel close to the provided `image.png`: a dark monochrome sci-fi control panel with a Hermes status area, animated signal/waveform, conversation log, and system log.

The first usable version focuses on being a fast, comfortable Discord bridge to Hermes Desktop. Voice features can be layered in after the text bridge and UI event flow are stable.

## Recommended Approach

Use Python with PySide6.

Reasons:

- Keeps the desktop UI, Discord bridge, STT/TTS, and later Windows automation in one Python runtime.
- Lighter and simpler than Electron for this project.
- Supports a custom frameless desktop window with precise styling.
- Fits the existing project direction in `SETUP.md` and `STEP.md`.

## MVP Scope

The MVP creates a desktop GUI with:

- Custom frameless window styled like `image.png`.
- Header with `H.E.R.M.E.S`, subtitle, clock, and close/minimize controls.
- Left status panel with Hermes emblem area, online/listening/thinking/speaking state, and waveform animation.
- Right conversation log showing user prompts and Hermes replies.
- Bottom system log for bridge events such as startup, Discord connection, sent command, and received response.
- Text command entry as the initial control surface.
- Optional disabled push-to-talk control in the UI, enabled later when STT is added.
- Discord configuration loaded from `.env`.

## Environment

The app reads:

- `DISCORD_BOT_TOKEN`
- `DISCORD_CHANNEL_ID`
- `DISCORD_APP_BOT_ID`

Secrets stay in `.env`. `.env.example` remains safe to commit and should only show empty keys.

## Data Flow

Initial text bridge:

```text
User types command in GUI
-> app posts command to Discord channel
-> Hermes Desktop/agent replies in Discord
-> app listens to channel messages
-> app filters replies from DISCORD_APP_BOT_ID when configured
-> GUI appends reply to conversation log
```

Later voice flow:

```text
Push-to-talk / wake word
-> microphone recording
-> STT
-> same Discord bridge
-> Hermes reply
-> TTS playback
```

## Main Components

`app.py`

- Starts the PySide6 application.
- Loads environment variables.
- Creates and wires the main window.

`hermes_bridge/config.py`

- Reads `.env`.
- Validates required Discord settings.
- Avoids printing secret values.

`hermes_bridge/discord_bridge.py`

- Sends user commands to Discord.
- Listens for channel messages.
- Emits UI-safe events for connection, errors, and replies.

`hermes_bridge/ui/main_window.py`

- Builds the custom desktop HUD.
- Owns visible state, logs, buttons, and text input.

`hermes_bridge/ui/styles.py`

- Contains the QSS styling for the monochrome Hermes look.

## Error Handling

- If `.env` is missing required Discord settings, show a clear error in the system log and keep the UI open.
- If Discord connection fails, show disconnected state and allow retry.
- If sending a command fails, keep the command in the input box and show the error.
- Never display the Discord bot token in logs.

## Testing

Use focused tests for non-visual behavior first:

- Config loads required keys from environment.
- Missing config reports safe, readable validation errors.
- Discord message filtering ignores non-Hermes bot messages when `DISCORD_APP_BOT_ID` is set.
- User command formatting is stable before sending to Discord.

Manual verification for the GUI:

- App opens as a desktop window.
- The layout matches the reference direction: left status panel, right conversation log, bottom system log.
- Text does not overlap at common desktop sizes.
- Close/minimize controls work.
- Missing `.env` values do not crash the app.

## Out Of Scope For MVP

- Wake word.
- Full STT/TTS voice loop.
- Windows GUI automation.
- Packaging to `.exe`.
- Pixel-perfect reproduction of the reference image beyond the core layout, mood, and interaction model.

These should come after the Discord text bridge is stable.
