"""Library path resolution for the native EVP wrapper."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Iterable, Optional


class LibraryNotFoundError(FileNotFoundError):
    """Raised when the native libevp wrapper cannot be found."""


def _candidate_library_names() -> list[str]:
    system = platform.system().lower()
    if "windows" in system:
        return ["libevp_wrapper.dll", "evp_wrapper.dll"]
    if "darwin" in system:
        return ["libevp_wrapper.dylib", "libevp_wrapper.so"]
    return ["libevp_wrapper.so"]


def _iter_candidates(explicit_path: Optional[str]) -> Iterable[Path]:
    package_dir = Path(__file__).resolve().parent
    project_root = package_dir.parent.parent.parent
    cwd = Path.cwd()

    if explicit_path:
        yield Path(explicit_path).expanduser()

    env_paths = [
        os.getenv("PYLIBEVP_LIB_PATH"),
        os.getenv("TALISMAN_EVP_LIB_PATH"),
    ]
    for env_path in env_paths:
        if env_path:
            yield Path(env_path).expanduser()

    for lib_name in _candidate_library_names():
        yield package_dir / "bin" / lib_name
        yield package_dir / lib_name
        yield cwd / lib_name
        yield project_root / "dvsku_libevp" / "libevp" / "build" / lib_name
        yield project_root / "libevp" / "build" / lib_name


def resolve_library_path(explicit_path: Optional[str] = None) -> Path:
    """Resolve the native wrapper path from explicit, env, and known locations."""
    checked_paths = []
    for candidate in _iter_candidates(explicit_path):
        candidate = candidate.resolve()
        checked_paths.append(str(candidate))
        if candidate.exists() and candidate.is_file():
            return candidate

    hints = [
        "Native wrapper not found.",
        "Build libevp_wrapper using CMake in dvsku_libevp/libevp and set PYLIBEVP_LIB_PATH.",
        "Checked paths:",
    ]
    hints.extend(f"- {path}" for path in checked_paths)
    raise LibraryNotFoundError("\n".join(hints))
