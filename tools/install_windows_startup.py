from __future__ import annotations

import os
import sys
from pathlib import Path

STARTUP_FILE_NAME = "Hermes Voice.bat"


def startup_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not set; cannot find Windows Startup folder.")
    return (
        Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    )


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    python_exe = pythonw if pythonw.exists() else Path(sys.executable)
    app_path = project_root / "app.py"
    startup_path = startup_dir() / STARTUP_FILE_NAME
    startup_path.parent.mkdir(parents=True, exist_ok=True)

    startup_path.write_text(
        "@echo off\n"
        f'cd /d "{project_root}"\n'
        f'start "" "{python_exe}" "{app_path}" --start-minimized --voice-mode\n',
        encoding="utf-8",
    )

    print(f"Installed Hermes startup launcher: {startup_path}")
    print("Hermes will start minimized with voice mode after Windows login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
