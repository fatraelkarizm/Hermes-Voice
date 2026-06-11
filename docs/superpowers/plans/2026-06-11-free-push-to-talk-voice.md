# Free Push-To-Talk Voice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add free local push-to-talk voice input to the PySide6 Hermes Voice Bridge.

**Architecture:** Voice input is isolated under `hermes_bridge/voice`. The UI emits press/release signals, a voice worker records and transcribes off the UI thread, and completed transcripts are submitted through the existing Discord command signal.

**Tech Stack:** Python 3.11, PySide6, sounddevice, numpy, faster-whisper, pytest.

---

## Tasks

### Task 1: Voice Audio Utilities

**Files:**
- Create: `hermes_bridge/voice/audio.py`
- Create: `hermes_bridge/voice/__init__.py`
- Create: `tests/test_voice_audio.py`

- [ ] Write tests for converting float audio to PCM16 bytes and writing a WAV file.
- [ ] Run `python -m pytest tests/test_voice_audio.py -v` and verify failure because the module does not exist.
- [ ] Implement `float32_to_pcm16` and `write_wav`.
- [ ] Run `python -m pytest tests/test_voice_audio.py -v` and verify pass.

### Task 2: Transcript Normalization

**Files:**
- Create: `hermes_bridge/voice/transcriber.py`
- Create: `tests/test_voice_transcriber.py`

- [ ] Write tests for joining segment text and stripping whitespace.
- [ ] Run `python -m pytest tests/test_voice_transcriber.py -v` and verify failure because the module does not exist.
- [ ] Implement `normalize_segments` and lazy `WhisperTranscriber`.
- [ ] Run `python -m pytest tests/test_voice_transcriber.py -v` and verify pass.

### Task 3: Push-To-Talk Worker And UI Wiring

**Files:**
- Create: `hermes_bridge/voice/input_worker.py`
- Modify: `hermes_bridge/ui/main_window.py`
- Modify: `app.py`
- Modify: `requirements.txt`
- Modify: `.env.example`

- [ ] Add free voice dependencies.
- [ ] Enable `HOLD TO TALK` and wire press/release signals.
- [ ] Add a voice worker that records on press, transcribes on release, and emits transcript/errors.
- [ ] Connect transcript output to existing Discord command submission.
- [ ] Log recording/transcribing states in the UI.

### Task 4: Verification

**Files:**
- Modify as needed based on test output.

- [ ] Run `python -m pytest -v`.
- [ ] Run `python -m compileall app.py hermes_bridge`.
- [ ] Run a headless UI smoke test.
- [ ] Tell the user how to install dependencies and manually test the mic.
