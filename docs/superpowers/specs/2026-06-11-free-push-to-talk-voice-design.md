# Free Push-To-Talk Voice Design

## Goal

Add a free local push-to-talk voice input path to Hermes Voice Bridge. The user holds the UI button, speaks a command, releases the button, and the app transcribes the audio locally before sending the text through the existing Discord bridge.

## Scope

The MVP implements voice input only:

- Enable the existing `HOLD TO TALK` button.
- Record microphone audio while the button is held.
- Save audio to a temporary WAV file.
- Transcribe the WAV file with local `faster-whisper`.
- Submit the transcript through the existing Discord bridge.
- Show clear status and system logs for recording, transcribing, errors, and empty transcripts.

TTS is not included in this MVP. It will be added after voice input is stable.

## Free Stack

- `sounddevice` for microphone recording.
- `numpy` for audio buffers.
- `wave` from the Python standard library for WAV output.
- `faster-whisper` for local speech-to-text.

## Runtime Behavior

```text
Hold button
-> start recording
-> release button
-> stop recording
-> write temp WAV
-> transcribe locally
-> submit transcript to Discord bridge
```

The app uses the existing Discord formatting logic, so when `DISCORD_APP_BOT_ID` is set the command is sent as a mention to Agentic.

## Error Handling

- If microphone access fails, log the error and return to `ONLINE`.
- If the transcript is empty, log that no speech was detected and do not send a Discord command.
- If `faster-whisper` is missing or model download fails, log the error without crashing the GUI.
- The Whisper model is loaded lazily on the first transcription.

## Configuration

Optional `.env` keys:

- `WHISPER_MODEL_SIZE=base`
- `VOICE_SAMPLE_RATE=16000`

Defaults are chosen for free local use and reasonable CPU performance.

## Verification

Automated tests cover WAV writing and transcript normalization. Manual verification covers microphone capture and local Whisper transcription.
