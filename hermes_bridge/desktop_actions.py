from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable
import os
from pathlib import Path
import re
import shutil
import subprocess
import webbrowser


@dataclass(frozen=True)
class DesktopAction:
    kind: str
    name: str
    target: str


@dataclass(frozen=True)
class AppCandidate:
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

OPEN_PREFIXES = (
    "open ",
    "buka ",
    "bukain ",
    "launch ",
    "start ",
    "jalanin ",
    "jalankan ",
)

APP_ALIASES = {
    "vscode": ("visual studio code", "vs code", "code"),
    "vs code": ("visual studio code", "code"),
}


def _normalize_name(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _strip_app_words(target: str) -> str:
    normalized = _normalize_name(target)
    for prefix in ("aplikasi ", "app ", "application "):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return normalized


def _query_terms(target: str) -> tuple[str, ...]:
    normalized = _strip_app_words(target)
    aliases = APP_ALIASES.get(normalized, ())
    terms = (normalized, *aliases)
    unique_terms = []
    for term in terms:
        if term and term not in unique_terms:
            unique_terms.append(term)
    return tuple(unique_terms)


def _candidate_names(candidate: AppCandidate) -> tuple[str, ...]:
    display_name = _normalize_name(candidate.name)
    return (display_name,) if display_name else ()


def _app_candidates_from_start_menu() -> tuple[AppCandidate, ...]:
    roots = [
        Path(os.environ[key]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        for key in ("APPDATA", "PROGRAMDATA")
        if os.environ.get(key)
    ]
    candidates: list[AppCandidate] = []
    seen_targets: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for shortcut in root.rglob("*.lnk"):
            target = str(shortcut)
            if target in seen_targets:
                continue
            seen_targets.add(target)
            candidates.append(AppCandidate(name=shortcut.stem, target=target))
    return tuple(candidates)


def _resolve_dynamic_app(
    target: str,
    app_candidates: Iterable[AppCandidate],
) -> DesktopAction | None:
    terms = _query_terms(target)
    if not terms:
        return None

    exact_matches = _dedupe_candidates(
        [
            candidate
            for candidate in app_candidates
            if any(term == name for term in terms for name in _candidate_names(candidate))
        ]
    )
    if len(exact_matches) == 1:
        match = exact_matches[0]
        return DesktopAction(kind="app", name=match.name, target=match.target)
    if len(exact_matches) > 1:
        names = ", ".join(candidate.name for candidate in exact_matches[:5])
        return DesktopAction(kind="app_ambiguous", name=names, target="")

    fuzzy_matches = _dedupe_candidates(
        [
            candidate
            for candidate in app_candidates
            if any(
                len(term) >= 3 and (name.startswith(term) or term in name)
                for term in terms
                for name in _candidate_names(candidate)
            )
        ]
    )
    if len(fuzzy_matches) == 1:
        match = fuzzy_matches[0]
        return DesktopAction(kind="app", name=match.name, target=match.target)
    if len(fuzzy_matches) > 1:
        names = ", ".join(candidate.name for candidate in fuzzy_matches[:5])
        return DesktopAction(kind="app_ambiguous", name=names, target="")

    executable = shutil.which(_strip_app_words(target))
    if executable is not None:
        name = _strip_app_words(target) or target.strip()
        return DesktopAction(kind="app", name=name, target=executable)

    return None


def _dedupe_candidates(candidates: Iterable[AppCandidate]) -> list[AppCandidate]:
    deduped: list[AppCandidate] = []
    seen_names: set[str] = set()
    for candidate in candidates:
        key = _normalize_name(candidate.name)
        if key in seen_names:
            continue
        seen_names.add(key)
        deduped.append(candidate)
    return deduped


def parse_desktop_action(
    command: str,
    app_candidates: Iterable[AppCandidate] | None = None,
) -> DesktopAction | None:
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

    if target.startswith(("http://", "https://")):
        return DesktopAction(kind="url", name=target, target=target)

    if app_candidates is not None:
        dynamic_action = _resolve_dynamic_app(target, app_candidates)
        if dynamic_action is not None:
            return dynamic_action

    if target in APPS:
        name, executable = APPS[target]
        return DesktopAction(kind="app", name=name, target=executable)

    return None


def parse_reply_action(reply: str) -> DesktopAction | None:
    text = reply.strip()
    navigate_match = re.search(
        r"browser_navigate\s*:\s*[\"'](?P<url>https?://[^\"']+)[\"']",
        text,
        flags=re.IGNORECASE,
    )
    if navigate_match is not None:
        url = navigate_match.group("url")
        return DesktopAction(kind="url", name=url, target=url)

    url_match = re.search(r"https?://[^\s>)\"']+", text)
    if url_match is not None and re.search(
        r"\b(done|opened|kebuka|dibuka|buka|open)\b", text, flags=re.IGNORECASE
    ):
        url = url_match.group(0)
        return DesktopAction(kind="url", name=url, target=url)

    return None


class DesktopActionRunner:
    def __init__(self, open_url=None, open_app=None, app_candidates=None) -> None:
        self._open_url = open_url or webbrowser.open
        self._open_app = open_app or self._open_app
        self._app_candidates = (
            app_candidates
            if app_candidates is not None
            else _app_candidates_from_start_menu()
        )

    def run(self, command: str) -> DesktopActionResult:
        action = parse_desktop_action(command, self._app_candidates)
        return self._run_action(action, opening_word="Opening")

    def run_reply(self, reply: str) -> DesktopActionResult:
        action = parse_reply_action(reply)
        return self._run_action(action, opening_word="Opened")

    def _run_action(
        self, action: DesktopAction | None, opening_word: str
    ) -> DesktopActionResult:
        if action is None:
            return DesktopActionResult(handled=False)

        if action.kind == "app_ambiguous":
            return DesktopActionResult(
                handled=True,
                message=f"Which app should I open: {action.name}?",
            )

        if action.kind == "url":
            self._open_url(action.target)
        else:
            self._open_app(action.target)

        return DesktopActionResult(handled=True, message=f"{opening_word} {action.name}.")

    @staticmethod
    def _open_app(target: str) -> None:
        if os.name == "nt":
            subprocess.Popen([target], shell=True)
            return
        subprocess.Popen([target])
