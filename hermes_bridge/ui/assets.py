from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_asset_path(filename: str) -> Path:
    root = project_root()
    requested = root / filename
    if requested.exists():
        return requested

    requested_stem = Path(filename).stem.lower()
    for candidate in root.iterdir():
        if candidate.is_file() and candidate.stem.lower() == requested_stem:
            return candidate

    return requested
