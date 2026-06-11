from __future__ import annotations

import os
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
    startup_path = startup_dir() / STARTUP_FILE_NAME
    if startup_path.exists():
        startup_path.unlink()
        print(f"Removed Hermes startup launcher: {startup_path}")
    else:
        print(f"Hermes startup launcher is not installed: {startup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
