from pathlib import Path

from tools.install_windows_startup import startup_launcher_text


def test_startup_launcher_uses_hidden_voice_launcher():
    project_root = Path("E:/Hermes-Voice")
    python_exe = project_root / ".venv" / "Scripts" / "pythonw.exe"

    launcher = startup_launcher_text(project_root, python_exe)

    assert "start_hermes_hidden.py" in launcher
    assert "--start-minimized" not in launcher
    assert "--voice-mode" not in launcher
