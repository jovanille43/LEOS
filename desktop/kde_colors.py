"""User-scoped KDE Plasma color-scheme export and explicit application.

This module only creates LEOS-owned .colors files under XDG_DATA_HOME and
uses KDE's dedicated plasma-apply-colorscheme executable. It never edits
system files, installs a Plasma Style, changes the desktop layout, or runs
commands through a shell.
"""
from __future__ import annotations

import configparser
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from desktop.themes import THEME_PALETTES, palette_for_theme, validate_palette

SCHEMA_VERSION = 1
MANAGED_BY = "LEOS Theme Manager"
THEME_NAMES = {
    "leos-original": "LEOS Original",
    "light": "LEOS Light",
    "cyan": "LEOS Cyan",
    "magenta": "LEOS Magenta",
    "gaming": "LEOS Gaming",
}
SCHEME_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
THEME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
NEGATIVE = "240,82,104"
NEUTRAL = "230,174,69"
POSITIVE = "61,201,139"


def _rgb(hex_color: str) -> str:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", hex_color):
        raise ValueError("Invalid RGB hex color")
    return ",".join(str(int(hex_color[index:index + 2], 16)) for index in (1, 3, 5))


def _luminance(hex_color: str) -> float:
    values = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in values
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_text(background: str) -> str:
    return "#0F1117" if _luminance(background) > 0.42 else "#FFFFFF"


def _color_set(
    background: str,
    alternate: str,
    foreground: str,
    muted: str,
    primary: str,
    secondary: str,
) -> dict[str, str]:
    return {
        "BackgroundAlternate": _rgb(alternate),
        "BackgroundNormal": _rgb(background),
        "DecorationFocus": _rgb(primary),
        "DecorationHover": _rgb(secondary),
        "ForegroundActive": _rgb(primary),
        "ForegroundInactive": _rgb(muted),
        "ForegroundLink": _rgb(primary),
        "ForegroundNegative": NEGATIVE,
        "ForegroundNeutral": NEUTRAL,
        "ForegroundNormal": _rgb(foreground),
        "ForegroundPositive": POSITIVE,
        "ForegroundVisited": _rgb(secondary),
    }


def build_colorscheme(theme: str) -> str:
    """Serialize one built-in LEOS palette into KDE's standard .colors format."""
    if theme not in THEME_PALETTES or not THEME_PATTERN.fullmatch(theme):
        raise ValueError(f"Unknown LEOS theme: {theme}")
    palette = palette_for_theme(theme)
    if not validate_palette(palette):
        raise ValueError("Invalid LEOS palette")
    name = THEME_NAMES[theme]
    background = palette["background"]
    surface = palette["surface"]
    elevated = palette["surface_elevated"]
    text = palette["text"]
    muted = palette["muted_text"]
    primary = palette["accent_primary"]
    secondary = palette["accent_secondary"]
    selected_text = _contrast_text(primary)

    groups = {
        "Colors:Window": _color_set(background, surface, text, muted, primary, secondary),
        "Colors:View": _color_set(surface, elevated, text, muted, primary, secondary),
        "Colors:Button": _color_set(surface, elevated, text, muted, primary, secondary),
        "Colors:Selection": _color_set(primary, secondary, selected_text, selected_text, primary, secondary),
        "Colors:Tooltip": _color_set(elevated, surface, text, muted, primary, secondary),
        "Colors:Complementary": _color_set(background, surface, text, muted, primary, secondary),
        "Colors:Header": _color_set(elevated, surface, text, muted, primary, secondary),
    }
    lines = [
        "# LEOS-managed KDE Plasma color scheme.",
        "# Generated from the matching palette in desktop/themes.py.",
        "",
        "[General]",
        f"ColorScheme=LEOS-{theme}",
        f"Name={name}",
        f"AccentColor={_rgb(primary)}",
        "shadeSortColumn=true",
        "",
        "[KDE]",
        "contrast=4",
    ]
    for group, values in groups.items():
        lines.extend(["", f"[{group}]"])
        lines.extend(f"{key}={value}" for key, value in values.items())
    lines.extend([
        "",
        "[WM]",
        f"activeBackground={_rgb(background)}",
        f"activeBlend={_rgb(text)}",
        f"activeForeground={_rgb(text)}",
        f"inactiveBackground={_rgb(surface)}",
        f"inactiveBlend={_rgb(muted)}",
        f"inactiveForeground={_rgb(muted)}",
        "",
        "[LEOS]",
        f"ManagedBy={MANAGED_BY}",
        f"ThemeId={theme}",
        f"SchemaVersion={SCHEMA_VERSION}",
        "",
    ])
    return "\n".join(lines)


class KdeColorSchemeManager:
    """Install and explicitly apply LEOS color schemes for the current user."""

    def __init__(
        self,
        data_home: Path | None = None,
        config_home: Path | None = None,
        state_home: Path | None = None,
        apply_executable: str | None = None,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self.data_home = data_home or Path(
            os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        )
        self.config_home = config_home or Path(
            os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        )
        self.state_home = state_home or Path(
            os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
        )
        self.scheme_dir = self.data_home / "color-schemes"
        self.config_file = self.config_home / "kdeglobals"
        self.state_file = self.state_home / "leos" / "kde-color-scheme.json"
        self.apply_executable = apply_executable
        self.runner = runner or subprocess.run

    @staticmethod
    def scheme_id(theme: str) -> str:
        if theme not in THEME_NAMES:
            raise ValueError(f"Unknown LEOS theme: {theme}")
        return f"LEOS-{theme}"

    def tool_available(self) -> bool:
        return bool(self.apply_executable or shutil.which("plasma-apply-colorscheme"))

    def current_scheme(self) -> str | None:
        if self.config_file.is_symlink() or not self.config_file.is_file():
            return None
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        try:
            parser.read(self.config_file, encoding="utf-8")
            value = parser.get("General", "ColorScheme", fallback="").strip()
        except (OSError, configparser.Error):
            return None
        if not value or len(value) > 80 or any(ch in value for ch in ("/", "\\", "\n", "\r")):
            return None
        return value

    def _read_state(self) -> dict[str, Any]:
        if self.state_file.is_symlink() or not self.state_file.is_file():
            return {}
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if (
            not isinstance(state, dict)
            or type(state.get("schema_version")) is not int
            or state.get("schema_version") != SCHEMA_VERSION
            or state.get("managed_by") != MANAGED_BY
        ):
            return {}
        previous = state.get("previous_scheme")
        if previous is not None and (
            not isinstance(previous, str)
            or not previous
            or len(previous) > 80
            or any(ch in previous for ch in ("/", "\\", "\n", "\r"))
        ):
            return {}
        return state

    def can_restore(self) -> bool:
        previous = self._read_state().get("previous_scheme")
        return isinstance(previous, str) and bool(previous)

    def install_scheme(self, theme: str) -> Path:
        """Install a user-scoped scheme without overwriting any differing file."""
        scheme_id = self.scheme_id(theme)
        if self.scheme_dir.is_symlink():
            raise ValueError("Symbolic-link color-scheme directories are not accepted")
        self.scheme_dir.mkdir(parents=True, exist_ok=True)
        if self.scheme_dir.is_symlink():
            raise ValueError("Symbolic-link color-scheme directories are not accepted")
        destination = self.scheme_dir / f"{scheme_id}.colors"
        if destination.is_symlink():
            raise ValueError("Symbolic-link color-scheme files are not accepted")
        payload = build_colorscheme(theme)
        if destination.exists():
            if not destination.is_file():
                raise ValueError("The existing color-scheme path is not a regular file")
            existing = destination.read_text(encoding="utf-8")
            if existing != payload:
                raise FileExistsError(
                    "A different file already uses this LEOS color-scheme name; it was left untouched."
                )
            return destination

        fd, temporary = tempfile.mkstemp(prefix="leos-colors.", suffix=".tmp", dir=self.scheme_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o644)
            os.replace(temporary, destination)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
        return destination

    def _write_state(self, state: dict[str, Any]) -> None:
        if self.state_file.is_symlink():
            raise ValueError("Symbolic-link LEOS theme state files are not accepted")
        if self.state_file.exists() and not self._read_state():
            raise ValueError("Existing LEOS KDE theme state is invalid; it was left untouched")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if self.state_file.parent.is_symlink():
            raise ValueError("Symbolic-link LEOS theme state directories are not accepted")
        payload = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
        fd, temporary = tempfile.mkstemp(prefix="kde-theme.", suffix=".tmp", dir=self.state_file.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.state_file)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    def _run_apply(self, scheme: str) -> None:
        if not isinstance(scheme, str) or not scheme or len(scheme) > 80:
            raise ValueError("Invalid KDE color-scheme identifier")
        executable = self.apply_executable or shutil.which("plasma-apply-colorscheme")
        if not executable:
            raise FileNotFoundError("plasma-apply-colorscheme is unavailable")
        try:
            result = self.runner(
                [executable, scheme],
                shell=False,
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("KDE did not finish applying the color scheme in time") from exc
        if result.returncode != 0:
            detail = (getattr(result, "stderr", "") or "").strip()
            raise RuntimeError(detail or "KDE refused to apply this color scheme")

    def apply_theme(self, theme: str) -> str:
        """Apply after explicit confirmation in the caller's UI."""
        scheme_id = self.scheme_id(theme)
        if not self.tool_available():
            raise FileNotFoundError("plasma-apply-colorscheme is unavailable")
        if self.state_file.is_symlink():
            raise ValueError("Symbolic-link LEOS theme state files are not accepted")
        state = self._read_state()
        current = self.current_scheme()
        if current is None:
            raise RuntimeError(
                "The active KDE color scheme cannot be identified; no theme was applied."
            )
        leos_ids = {self.scheme_id(key) for key in THEME_NAMES}
        previous = state.get("previous_scheme")
        if current not in leos_ids:
            previous = current
        elif not previous:
            raise RuntimeError(
                "A LEOS color scheme is active but its previous KDE scheme is unavailable."
            )

        self.install_scheme(theme)
        # Persist the rollback target before changing KDE. If the command fails
        # or the process is interrupted, the previous scheme remains recoverable.
        self._write_state({
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous_scheme": previous,
            "last_applied": scheme_id,
            "apply_pending": True,
        })
        self._run_apply(scheme_id)
        self._write_state({
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous_scheme": previous,
            "last_applied": scheme_id,
            "apply_pending": False,
        })
        return f"Schéma KDE « {THEME_NAMES[theme]} » appliqué."

    def restore_previous_theme(self) -> str:
        """Restore the last non-LEOS scheme captured before a LEOS application."""
        state = self._read_state()
        previous = state.get("previous_scheme")
        if not isinstance(previous, str) or not previous:
            raise FileNotFoundError("No previous KDE color scheme is available")
        if not self.tool_available():
            raise FileNotFoundError("plasma-apply-colorscheme is unavailable")
        self._run_apply(previous)
        if self.state_file.is_symlink():
            raise ValueError("Symbolic-link LEOS theme state files are not accepted")
        self.state_file.unlink(missing_ok=True)
        return f"Thème KDE précédent restauré : {previous}."
