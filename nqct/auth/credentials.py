"""Load and save ~/.nqct/credentials.json profiles."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CREDENTIALS_DIR = Path.home() / ".nqct"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
DEFAULT_PROFILE = "default"


def credentials_path() -> Path:
    return CREDENTIALS_FILE


def load_profile(name: str = DEFAULT_PROFILE) -> dict[str, str]:
    """Return a named credentials profile or raise ``FileNotFoundError``."""
    path = credentials_path()
    if path.is_file() and path.stat().st_mode & 0o077:
        import warnings

        warnings.warn(f"Credentials file {path} is world/group accessible", stacklevel=2)
    if not path.is_file():
        raise FileNotFoundError(
            f"No credentials file at {path}. Call NQCTClient.save_account() or set NQCT_API_KEY."
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if name not in data:
        raise KeyError(f"Profile {name!r} not found in {path}")
    profile = data[name]
    if not isinstance(profile, dict):
        raise ValueError(f"Profile {name!r} is not an object")
    return {str(k): str(v) for k, v in profile.items()}


def save_profile(
    *,
    url: str,
    api_key: str | None = None,
    token: str | None = None,
    refresh_token: str | None = None,
    name: str = DEFAULT_PROFILE,
) -> Path:
    """Persist a credentials profile with file mode ``0600``."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    path = credentials_path()

    existing: dict[str, Any] = {}
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))

    profile: dict[str, str] = {"url": url.rstrip("/")}
    if api_key is not None:
        profile["api_key"] = api_key
    if token is not None:
        profile["token"] = token
    if refresh_token is not None:
        profile["refresh_token"] = refresh_token

    existing[name] = profile
    path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    if path.stat().st_mode & 0o077:
        import warnings

        warnings.warn(f"Credentials file {path} is world/group accessible", stacklevel=2)
    return path


def delete_profile(name: str = DEFAULT_PROFILE) -> None:
    path = credentials_path()
    if not path.is_file():
        return
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    data.pop(name, None)
    if data:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.chmod(path, 0o600)
    else:
        path.unlink(missing_ok=True)
