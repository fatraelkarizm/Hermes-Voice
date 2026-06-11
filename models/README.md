# Wake Word Models

Run this from the project root to install the ready-made "Hey Hermes" model:

```powershell
.\.venv\Scripts\python.exe tools\setup_wakeword.py
```

The app reads the model path from `HERMES_OPENWAKEWORD_MODELS`.
Model binaries are ignored by git so the repo does not store large downloaded files.
