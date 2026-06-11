from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_asset_path(filename: str) -> Path:
    return project_root() / filename

