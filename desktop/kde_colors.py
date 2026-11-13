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

from desktop.themes import (
    THEME_PALETTES, palette_for_theme, palette_for_colors, normalize_color, validate_palette,
)
from leos_core.paths import (
    config_home as xdg_config_home,
    data_home as xdg_data_home,
    state_home as xdg_state_home,
)

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
MAX_KDE_CONFIG_BYTES = 1024 * 1024
MAX_KDE_STATE_BYTES = 64 * 1024
MAX_KDE_SCHEME_BYTES = 512 * 1024
NEGATIVE = "240,82,104"
NEUTRAL = "230,174,69"
POSITIVE = "61,201,139"


def _read_bounded_text(path: Path, max_bytes: int) -> str | None:
    if type(max_bytes) is not int or max_bytes < 0:
        return None
    if path.is_symlink() or path.parent.is_symlink():
        return None
    try:
        with path.open("rb") as stream:
            raw = stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return None
        return raw.decode("utf-8")
    except (OSError, UnicodeError):
        return None


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
    """Choose the darker or lighter selection text with the stronger contrast."""
    luminance = _luminance(background)
    dark_contrast = (luminance + 0.05) / (0.05 + 0.0) if luminance >= 0.0 else 1.0
    light_contrast = 1.05 / (luminance + 0.05)
    return "#0F1117" if dark_contrast >= light_contrast else "#FFFFFF"


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


def _build_colorscheme(palette: dict[str, str], scheme_id: str, name: str, theme_id: str) -> str:
    """Serialize a validated palette into KDE's standard .colors format."""
    if not SCHEME_ID_PATTERN.fullmatch(scheme_id) or not validate_palette(palette):
        raise ValueError("Invalid LEOS color scheme")
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
        f"ColorScheme={scheme_id}",
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
        f"ThemeId={theme_id}",
        f"SchemaVersion={SCHEMA_VERSION}",
        "",
    ])
    return "\n".join(lines)


def build_colorscheme(theme: str) -> str:
    """Serialize one legacy built-in palette into KDE's standard .colors format."""
    if theme not in THEME_PALETTES or not THEME_PATTERN.fullmatch(theme):
        raise ValueError(f"Unknown LEOS theme: {theme}")
    return _build_colorscheme(
        palette_for_theme(theme), f"LEOS-{theme}", THEME_NAMES[theme], theme
    )


def custom_scheme_id(color_a: str, color_b: str) -> str:
    """Return a deterministic, filesystem-safe ID for a custom A/B pair."""
    first = normalize_color(color_a)
    second = normalize_color(color_b)
    return f"LEOS-{first[1:]}-{second[1:]}"


def build_custom_colorscheme(color_a: str, color_b: str) -> str:
    """Serialize the user's custom A/B gradient into a KDE color scheme."""
    first = normalize_color(color_a)
    second = normalize_color(color_b)
    return _build_colorscheme(
        palette_for_colors(first, second),
        custom_scheme_id(first, second),
        "LEOS personnalisé",
        "custom",
    )


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
            xdg_data_home()
        )
        self.config_home = config_home or Path(
            xdg_config_home()
        )
        self.state_home = state_home or Path(
            xdg_state_home()
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
        content = _read_bounded_text(self.config_file, MAX_KDE_CONFIG_BYTES)
        if content is None:
            return None
        try:
            parser.read_string(content)
            value = parser.get("General", "ColorScheme", fallback="").strip()
        except configparser.Error:
            return None
        if not value or len(value) > 80 or any(ch in value for ch in ("/", "\\", "\n", "\r")):
            return None
        return value

    def _read_state(self) -> dict[str, Any]:
        if self.state_file.is_symlink() or not self.state_file.is_file():
            return {}
        content = _read_bounded_text(self.state_file, MAX_KDE_STATE_BYTES)
        if content is None:
            return {}
        try:
            state = json.loads(content)
        except json.JSONDecodeError:
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

    def _install_payload(self, scheme_id: str, payload: str) -> Path:
        """Install one validated user-scoped scheme without overwriting conflicts."""
        if not SCHEME_ID_PATTERN.fullmatch(scheme_id):
            raise ValueError("Invalid LEOS color-scheme identifier")
        if self.scheme_dir.is_symlink():
            raise ValueError("Symbolic-link color-scheme directories are not accepted")
        self.scheme_dir.mkdir(parents=True, exist_ok=True)
        if self.scheme_dir.is_symlink():
            raise ValueError("Symbolic-link color-scheme directories are not accepted")
        destination = self.scheme_dir / f"{scheme_id}.colors"
        if destination.is_symlink():
            raise ValueError("Symbolic-link color-scheme files are not accepted")
        if destination.exists():
            if not destination.is_file():
                raise ValueError("The existing color-scheme path is not a regular file")
            existing = _read_bounded_text(destination, MAX_KDE_SCHEME_BYTES)
            if existing is None:
                raise FileExistsError(
                    "Existing KDE color-scheme file cannot be safely inspected; it was left untouched."
                )
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

    def install_scheme(self, theme: str) -> Path:
        """Install a legacy named scheme for compatibility."""
        scheme_id = self.scheme_id(theme)
        return self._install_payload(scheme_id, build_colorscheme(theme))

    def install_custom_scheme(self, color_a: str, color_b: str) -> Path:
        """Install the selected A/B pair in the current user's KDE data directory."""
        scheme_id = custom_scheme_id(color_a, color_b)
        return self._install_payload(
            scheme_id, build_custom_colorscheme(color_a, color_b)
        )

    def _write_state(self, state: dict[str, Any]) -> None:
        if self.state_file.is_symlink():
            raise ValueError("Symbolic-link LEOS theme state files are not accepted")
        if self.state_file.exists() and not self._read_state():
            raise ValueError("Existing LEOS KDE theme state is invalid; it was left untouched")
        self.state_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.state_file.parent.is_symlink():
            raise ValueError("Symbolic-link LEOS theme state directories are not accepted")
        payload = (json.dumps(state, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if len(payload) > MAX_KDE_STATE_BYTES:
            raise ValueError("LEOS KDE theme state exceeds its storage limit")
        os.chmod(self.state_file.parent, 0o700)
        fd, temporary = tempfile.mkstemp(
            prefix="kde-theme.", suffix=".tmp", dir=self.state_file.parent
        )
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
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

    def _apply_scheme(self, scheme_id: str, payload: str, display_name: str) -> str:
        """Apply a validated LEOS scheme while preserving a non-LEOS rollback target."""
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
        is_leos_scheme = current in leos_ids or current.startswith("LEOS-")
        if not is_leos_scheme:
            previous = current
        elif not previous:
            raise RuntimeError(
                "A LEOS color scheme is active but its previous KDE scheme is unavailable."
            )

        self._install_payload(scheme_id, payload)
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
        return f"Schéma KDE « {display_name} » appliqué."

    def apply_theme(self, theme: str) -> str:
        """Apply a legacy named scheme after explicit confirmation in the caller's UI."""
        scheme_id = self.scheme_id(theme)
        return self._apply_scheme(
            scheme_id, build_colorscheme(theme), THEME_NAMES[theme]
        )

    def apply_custom_theme(self, color_a: str, color_b: str) -> str:
        """Apply the user's A/B gradient after explicit confirmation in the UI."""
        first = normalize_color(color_a)
        second = normalize_color(color_b)
        return self._apply_scheme(
            custom_scheme_id(first, second),
            build_custom_colorscheme(first, second),
            "LEOS personnalisé",
        )

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
