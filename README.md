# Hermes Voice Bridge

## Overview
Hermes Voice Bridge is a powerful, locally-hosted Windows desktop companion that bridges seamless voice interaction to a Discord-based AI agent (Hermes). It features wake-word detection, push-to-talk capabilities, real-time speech-to-text processing, and native desktop app/media control. Built with Python and modern UI frameworks, it acts as a smart local frontend that handles lightweight tasks on the host machine while delegating complex conversational AI to a cloud-hosted Discord bot.

## Problem Statement
In the evolving landscape of AI assistants, users often face a disconnect between web-based AI tools, desktop environments, and communication platforms like Discord. Traditional voice assistants are either entirely cloud-bound (with privacy concerns and latency) or lack deep integration with local desktop applications and community servers. There is a need for a hybrid solution that offers the privacy and speed of local wake-word detection and media control, coupled with the advanced conversational capabilities of a dedicated Discord AI agent, all accessible hands-free while gaming or working.

## Solution
Hermes Voice Bridge solves this by implementing a hybrid edge-cloud architecture:
- **Local Processing**: Wake-word detection (`openWakeWord`) and Speech-to-Text transcription (`faster-whisper`) are processed entirely on the local machine to ensure privacy, low latency, and offline command filtering.
- **Native Desktop Integration**: Media commands (Spotify, YouTube, local playback) and app launching are intercepted and executed locally without needing cloud API calls, providing instant responses.
- **Discord AI Bridge**: Complex queries and conversational inputs are intelligently forwarded to a Discord channel where the Hermes AI agent processes them and streams text-to-speech (TTS) replies back to the local desktop client.
- **Unobtrusive UX**: Designed to run minimized or hidden in the system tray, it activates only when needed, making it a perfect companion for multitasking and gaming.

## Key Features & Tech Stack

### Key Features
- **Hands-Free Wake-Word Detection**: Local "Hey Hermes" detection with fallback capabilities.
- **Real-Time Speech Transcription**: Fast and accurate voice-to-text conversion.
- **Local Desktop Actions**: Voice commands to open apps, play music via Spotify/YouTube, and control media playback natively.
- **Discord Integration**: Two-way communication bridge to Discord bots.
- **Smart Routing**: Intent recognition to route media/app commands locally and conversational queries to Discord.
- **Text-to-Speech (TTS) Replies**: Spoken responses from the AI agent.
- **Customizable Environment**: Fully configurable via `.env` (wake words, music providers, app aliases).
- **Windows Startup Integration**: Capable of running seamlessly as a background startup process.

### Tech Stack
- **Language**: Python 3.x
- **GUI Framework**: PySide6 (Qt for Python)
- **Voice / Audio**: `faster-whisper` (Speech-to-Text), `openwakeword` (Wake-Word Detection), `sounddevice`
- **Integrations**: `discord.py` (Discord API bridge), Spotify API, YouTube API
- **Testing & Tooling**: `pytest`, virtual environments (`venv`)

## Getting Started

### Prerequisites
- Python 3.9+ installed on your Windows machine.
- A Discord Bot Token and configured server/channel.

### Installation

1. **Clone the repository**
   ```powershell
   git clone https://github.com/fatraelkarizm/Hermes-Voice.git
   cd Hermes-Voice
   ```

2. **Set up the virtual environment**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. **Initialize the Wake-Word Model**
   ```powershell
   .\.venv\Scripts\python.exe tools\setup_wakeword.py
   ```

4. **Configuration**
   Create a `.env` file from the provided example and add your credentials:
   ```powershell
   cp .env.example .env
   ```
   *Edit `.env` to include your `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`, etc.*

### Running the App

**Visible GUI Mode:**
```powershell
.\.venv\Scripts\python.exe app.py --voice-mode
```

**Hidden / Background Mode:**
```powershell
.\.venv\Scripts\python.exe tools\start_hermes_hidden.py
```

**Windows Startup setup:**
```powershell
.\.venv\Scripts\python.exe tools\install_windows_startup.py
```

To interact, simply say: *"Hey Hermes"* followed by your command!

## Troubleshooting

Logs are written to `hermes-voice.log`. 
If the wake word does not trigger:
1. Run `tools\setup_wakeword.py` again.
2. Check `hermes-voice.log` for errors.
3. Lower `HERMES_OPENWAKEWORD_THRESHOLD` in `.env` if your microphone is quiet.
