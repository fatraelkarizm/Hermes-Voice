from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
import webbrowser


@dataclass(frozen=True)
class DesktopAction:
    kind: str
    name: str
    target: str


@dataclass(frozen=True)
class DesktopActionResult:
    handled: bool
    message: str = ""


WEBSITES = {
    "google": ("Google", "https://www.google.com"),
    "youtube": ("YouTube", "https://www.youtube.com"),
    "gmail": ("Gmail", "https://mail.google.com"),
    "github": ("GitHub", "https://github.com"),
    "chatgpt": ("ChatGPT", "https://chatgpt.com"),
}

APPS = {
    "chrome": ("Chrome", "chrome"),
    "discord": ("Discord", "discord"),
    "spotify": ("Spotify", "spotify"),
    "vscode": ("VS Code", "code"),
    "vs code": ("VS Code", "code"),
    "notepad": ("Notepad", "notepad"),
    "calculator": ("Calculator", "calc"),
}

OPEN_PREFIXES = ("open ", "buka ", "launch ", "start ")


def parse_desktop_action(command: str) -> DesktopAction | None:
    normalized = " ".join(command.lower().strip(" .,!?:;").split())
    target = ""
    for prefix in OPEN_PREFIXES:
        if normalized.startswith(prefix):
            target = normalized[len(prefix) :].strip()
            break
    if not target:
        return None

    if target in WEBSITES:
        name, url = WEBSITES[target]
        return DesktopAction(kind="url", name=name, target=url)

    if target in APPS:
        name, executable = APPS[target]
        return DesktopAction(kind="app", name=name, target=executable)

    if target.startswith(("http://", "https://")):
        return DesktopAction(kind="url", name=target, target=target)

    return None


class DesktopActionRunner:
    def __init__(self, open_url=None, open_app=None) -> None:
        self._open_url = open_url or webbrowser.open
        self._open_app = open_app or self._open_app

    def run(self, command: str) -> DesktopActionResult:
        action = parse_desktop_action(command)
        if action is None:
            return DesktopActionResult(handled=False)

        if action.kind == "url":
            self._open_url(action.target)
        else:
            self._open_app(action.target)

        return DesktopActionResult(handled=True, message=f"Opening {action.name}.")

    @staticmethod
    def _open_app(target: str) -> None:
        if os.name == "nt":
            subprocess.Popen([target], shell=True)
            return
        subprocess.Popen([target])
