from __future__ import annotations

import os
from pathlib import Path


class SingleInstanceLock:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._handle = None

    def acquire(self) -> bool:
        if self._handle is not None:
            return True

        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._handle = _acquire_lock(self._path)
        except OSError:
            return False
        return True

    def release(self) -> None:
        handle = self._handle
        if handle is None:
            return

        self._handle = None
        _release_lock(handle)


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    ERROR_ALREADY_EXISTS = 183

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (
        wintypes.LPVOID,
        wintypes.BOOL,
        wintypes.LPCWSTR,
    )
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL

    def _mutex_name(path: Path) -> str:
        resolved = str(path.resolve()).replace("\\", "_").replace(":", "")
        return rf"Local\{resolved}"

    def _acquire_lock(path: Path):
        handle = kernel32.CreateMutexW(None, False, _mutex_name(path))
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            raise OSError("another instance already holds the mutex")
        return handle

    def _release_lock(handle) -> None:
        kernel32.CloseHandle(handle)

else:
    import fcntl

    def _acquire_lock(path: Path):
        lock_file = path.open("a+b")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file

    def _release_lock(handle) -> None:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
