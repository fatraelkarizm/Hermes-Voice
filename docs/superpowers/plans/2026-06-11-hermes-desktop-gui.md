# Hermes Desktop GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable lightweight PySide6 desktop GUI bridge for Hermes Desktop via Discord.

**Architecture:** The app has a small tested core for config parsing, command formatting, and Discord reply filtering, plus a PySide6 GUI shell that can run even when Discord settings are missing. Discord integration lives behind a worker object so the UI stays responsive.

**Tech Stack:** Python 3.11, PySide6, discord.py, pytest.

---

## File Structure

- `requirements.txt`: Python dependencies.
- `app.py`: Application entry point.
- `hermes_bridge/config.py`: `.env` parsing and validation.
- `hermes_bridge/discord_bridge.py`: Discord formatting, filtering, and worker.
- `hermes_bridge/ui/main_window.py`: Desktop GUI.
- `hermes_bridge/ui/styles.py`: QSS style sheet.
- `tests/test_config.py`: Config tests.
- `tests/test_discord_bridge.py`: Discord helper tests.

## Tasks

### Task 1: Config Core

**Files:**
- Create: `hermes_bridge/config.py`
- Create: `tests/test_config.py`

- [ ] Write failing tests for loading valid `.env`, detecting missing required values, and keeping token text out of errors.
- [ ] Run `python -m pytest tests/test_config.py -v` and verify failure because `hermes_bridge.config` does not exist.
- [ ] Implement `DiscordSettings`, `ConfigError`, and `load_settings`.
- [ ] Run `python -m pytest tests/test_config.py -v` and verify pass.

### Task 2: Discord Helpers

**Files:**
- Create: `hermes_bridge/discord_bridge.py`
- Create: `tests/test_discord_bridge.py`

- [ ] Write failing tests for command formatting and reply filtering.
- [ ] Run `python -m pytest tests/test_discord_bridge.py -v` and verify failure because helpers do not exist.
- [ ] Implement `format_user_command` and `should_accept_message`.
- [ ] Run `python -m pytest tests/test_discord_bridge.py -v` and verify pass.

### Task 3: Desktop GUI

**Files:**
- Create: `hermes_bridge/ui/main_window.py`
- Create: `hermes_bridge/ui/styles.py`
- Create: `hermes_bridge/__init__.py`
- Create: `hermes_bridge/ui/__init__.py`
- Create: `app.py`
- Create: `requirements.txt`

- [ ] Implement the PySide6 frameless HUD-style main window.
- [ ] Wire text command input to the Discord worker when config is valid.
- [ ] Keep the UI open and log a safe error when config is missing.
- [ ] Run `python -m pytest -v`.
- [ ] Run `python app.py` manually to verify the GUI opens.

### Task 4: Final Verification

**Files:**
- Modify as needed based on verification output.

- [ ] Run `python -m pytest -v`.
- [ ] Run a Python import check for `app`, `hermes_bridge.config`, and `hermes_bridge.discord_bridge`.
- [ ] Report exact run commands to the user.
