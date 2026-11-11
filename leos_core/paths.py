"""Resolve standard XDG user directories from valid absolute environment values."""

from __future__ import annotations

import os
from pathlib import Path


def _xdg_home(variable: str, default: str) -> Path:
    """Use a configured absolute XDG directory, otherwise its home default."""
    configured = os.environ.get(variable, "").strip()
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_absolute():
            return candidate
    return Path.home() / default


def config_home() -> Path:
    """Return XDG_CONFIG_HOME or ~/.config."""
    return _xdg_home("XDG_CONFIG_HOME", ".config")


def data_home() -> Path:
    """Return XDG_DATA_HOME or ~/.local/share."""
    return _xdg_home("XDG_DATA_HOME", ".local/share")


def state_home() -> Path:
    """Return XDG_STATE_HOME or ~/.local/state."""
    return _xdg_home("XDG_STATE_HOME", ".local/state")
