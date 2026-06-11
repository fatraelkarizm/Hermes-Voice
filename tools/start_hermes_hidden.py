from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"
LOG_PATH = PROJECT_ROOT / "hermes-voice.log"


def pythonw_path() -> Path:
    candidate = Path(sys.executable).with_name("pythonw.exe")
    return candidate if candidate.exists() else Path(sys.executable)


def stop_existing_instances() -> None:
    result = subprocess.run(
        [
            "wmic",
            "process",
            "where",
            "commandline like '%Hermes-Voice%app.py%'",
            "get",
            "ProcessId",
            "/value",
        ],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if not line.startswith("ProcessId="):
            continue
        raw_pid = line.split("=", 1)[1].strip()
        if not raw_pid.isdigit():
            continue
        subprocess.run(
            ["taskkill", "/PID", raw_pid, "/F"],
            capture_output=True,
            text=True,
        )


def main() -> int:
    stop_existing_instances()
    executable = pythonw_path()
    command = [str(executable), str(APP_PATH), "--start-hidden", "--voice-mode"]
    process = subprocess.Popen(command, cwd=PROJECT_ROOT)
    time.sleep(1)

    if process.poll() is None:
        print(f"Hermes Voice started in hidden voice mode. PID: {process.pid}")
        print(f"Log file: {LOG_PATH}")
        return 0

    print(f"Hermes Voice exited immediately with code {process.returncode}.")
    print(
        f"Run this for visible errors: {Path(sys.executable)} {APP_PATH} --voice-mode"
    )
    return process.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
