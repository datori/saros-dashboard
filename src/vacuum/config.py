"""Credential and device configuration loaded from environment or .env file."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (parent of src/)
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

# Session file stores user_data plus a cached _base_url key to avoid
# the _get_iot_login_info() network round-trip on every command.
SESSION_FILE = Path(__file__).parent.parent.parent / ".roborock_session.json"


class ConfigError(Exception):
    pass


def get_username() -> str:
    username = os.getenv("ROBOROCK_USERNAME", "").strip()
    if not username:
        raise ConfigError(
            "ROBOROCK_USERNAME must be set. Copy .env.example to .env and fill in your credentials."
        )
    return username


def get_credentials() -> tuple[str, str]:
    """Return (username, password) from environment.

    Raises ConfigError if either is missing.
    """
    username = os.getenv("ROBOROCK_USERNAME", "").strip()
    password = os.getenv("ROBOROCK_PASSWORD", "").strip()
    if not username or not password:
        raise ConfigError(
            "ROBOROCK_USERNAME and ROBOROCK_PASSWORD must be set. "
            "Copy .env.example to .env and fill in your credentials."
        )
    return username, password


def get_device_name() -> str | None:
    """Return optional device name filter, or None to use first discovered device."""
    return os.getenv("ROBOROCK_DEVICE_NAME", "").strip() or None


def load_session() -> dict | None:
    """Load saved session from .roborock_session.json, or None if not present.

    The session dict contains the UserData fields plus an optional '_base_url'
    key holding the cached IOT base URL.
    """
    if SESSION_FILE.exists():
        with open(SESSION_FILE) as f:
            return json.load(f)
    return None


def save_session(user_data_dict: dict, base_url: str | None = None) -> None:
    """Persist session to .roborock_session.json.

    Merges the optional base_url into the session under '_base_url' so
    subsequent commands can skip the _get_iot_login_info() network call.
    """
    data = dict(user_data_dict)
    if base_url:
        data["_base_url"] = base_url
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, default=str, indent=2)
