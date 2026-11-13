"""Explicit, reversible application of the three LEOS KDE visual components.

The manager touches only the current user's KConfig files, calls KDE's native
Plasma Style helper, and asks KWin to reconfigure. It never writes into
/usr/share, never uses a shell, and preserves user changes made after LEOS was
applied. Resource export is handled separately by ThemeAssetManager.
"""
from __future__ import annotations

import configparser
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from desktop.plasma_style import PlasmaStyleManager
from desktop.theme_assets import ThemeAssetManager
from desktop.themes import THEME_PALETTES
from leos_core.paths import config_home as xdg_config_home
from leos_core.paths import state_home as xdg_state_home

SCHEMA_VERSION = 1
MANAGED_BY = "LEOS KDE Visual Theme Manager"
MAX_CONFIG_BYTES = 1024 * 1024
MAX_STATE_BYTES = 64 * 1024
THEME_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
AURORAE_LIBRARY = "org.kde.kwin.aurorae"


def _read_ini_value(path: Path, group: str, key: str) -> str | None:
    """Read one user KConfig entry without following symlinks or large files."""
    if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
        return None
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_CONFIG_BYTES + 1)
        if len(raw) > MAX_CONFIG_BYTES:
            return None
        content = raw.decode("utf-8")
    except (OSError, UnicodeError):
        return None

    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read_string(content)
    except configparser.Error:
        return None
    if not parser.has_section(group):
        return None
    for existing_key, value in parser.items(group):
        if existing_key.casefold() == key.casefold():
            value = value.strip()
            if not value or len(value) > 160:
                return None
            if any(character in value for character in ("/", "\\", "\n", "\r")):
                # IDs are never paths or arbitrary KConfig payloads.
                if existing_key.casefold() in {"theme", "name", "library"}:
                    if "/" in value or "\\" in value or "\n" in value or "\r" in value:
                        return None
            return value
    return None


def _valid_optional_config_value(value: Any) -> bool:
    return value is None or (
        isinstance(value, str)
        and len(value) <= 160
        and not any(character in value for character in ("\x00", "\n", "\r"))
    )


class KdeVisualThemeManager:
    """Apply and restore icons, Plasma Style and Aurorae as one LEOS theme."""

    def __init__(
        self,
        assets: ThemeAssetManager | None = None,
        plasma_style: PlasmaStyleManager | None = None,
        config_home: Path | None = None,
        state_home: Path | None = None,
        data_home: Path | None = None,
        runner: Callable[..., Any] | None = None,
        find_executable: Callable[[str], str | None] = shutil.which,
    ) -> None:
        self.assets = assets or ThemeAssetManager()
        self.config_home = Path(config_home) if config_home is not None else Path(xdg_config_home())
        self.state_home = Path(state_home) if state_home is not None else Path(xdg_state_home())
        self.data_home = Path(data_home) if data_home is not None else None
        self.kdeglobals = self.config_home / "kdeglobals"
        self.plasmarc = self.config_home / "plasmarc"
        self.kwinrc = self.config_home / "kwinrc"
        self.state_file = self.state_home / "leos" / "kde-visual-theme.json"
        self.runner = runner or subprocess.run
        self.find_executable = find_executable
        self._plasma_executable = find_executable("plasma-apply-desktoptheme")
        self.plasma_style = plasma_style or PlasmaStyleManager(
            config_home=self.config_home,
            state_home=self.state_home,
            apply_executable=self._plasma_executable,
            runner=self.runner,
        )

    def _state(self) -> dict[str, Any]:
        if self.state_file.is_symlink() or not self.state_file.is_file():
            return {}
        try:
            raw = self.state_file.read_bytes()
            if len(raw) > MAX_STATE_BYTES:
                return {}
            value = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {}
        if (
            not isinstance(value, dict)
            or type(value.get("schema_version")) is not int
            or value.get("schema_version") != SCHEMA_VERSION
            or value.get("managed_by") != MANAGED_BY
        ):
            return {}
        string_fields = (
            "theme",
            "previous_plasma",
            "last_icons",
            "last_plasma",
            "last_aurorae_library",
            "last_aurorae_theme",
        )
        optional_fields = (
            "previous_icons",
            "previous_aurorae_library",
            "previous_aurorae_theme",
        )
        for field in string_fields:
            if not isinstance(value.get(field), str) or not value[field] or len(value[field]) > 160:
                return {}
        if not THEME_ID_PATTERN.fullmatch(value["theme"]):
            return {}
        if any(not _valid_optional_config_value(value.get(field)) for field in optional_fields):
            return {}
        if type(value.get("apply_pending")) is not bool:
            return {}
        for field in ("restore_icons_done", "restore_plasma_done", "restore_aurorae_done"):
            if field in value and type(value[field]) is not bool:
                return {}
            value.setdefault(field, False)
        return value

    def can_restore(self) -> bool:
        return bool(self._state())

    def resources_available(self, theme: str) -> bool:
        if theme not in THEME_PALETTES:
            return False
        resources = self.assets.exported_kde_resource_paths_for_theme(
            theme, data_directory=self.data_home
        )
        return {
            "icon_theme_path",
            "plasma_theme_path",
            "aurorae_theme_path",
        }.issubset(resources)

    def _write_state(self, state: dict[str, Any]) -> None:
        if self.state_file.is_symlink():
            raise ValueError("LEOS KDE visual theme state cannot be a symbolic link")
        if self.state_file.exists() and not self._state():
            raise ValueError("Existing LEOS KDE visual theme state is invalid; it was left untouched")
        parent = self.state_file.parent
        if parent.is_symlink():
            raise ValueError("LEOS KDE visual theme state directory cannot be a symbolic link")
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(parent, 0o700)
        payload = (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(payload) > MAX_STATE_BYTES:
            raise ValueError("LEOS KDE visual theme state exceeds its size limit")
        descriptor, temporary = tempfile.mkstemp(
            prefix="kde-visual-theme.", suffix=".tmp", dir=parent
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_file)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    def _run(self, arguments: list[str], timeout: int = 12) -> None:
        try:
            result = self.runner(
                arguments,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("KDE n'a pas répondu dans le délai prévu") from error
        if result.returncode != 0:
            detail = (getattr(result, "stderr", "") or "").strip()
            raise RuntimeError(detail or "KDE a refusé le changement de thème")

    def _write_key(
        self,
        config_file: Path,
        group: str,
        key: str,
        value: str | None,
    ) -> None:
        if config_file.parent.is_symlink() or config_file.is_symlink():
            raise ValueError("Un fichier de configuration KDE symbolique ne sera pas modifié")
        executable = self.find_executable("kwriteconfig6")
        if not executable:
            raise FileNotFoundError("kwriteconfig6 est indisponible")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        arguments = [
            executable,
            "--file", str(config_file),
            "--group", group,
            "--key", key,
        ]
        if value is None:
            arguments.append("--delete")
        else:
            if not _valid_optional_config_value(value):
                raise ValueError("Valeur KConfig invalide")
            arguments.append(value)
        self._run(arguments)

    def _refresh_icons(self) -> bool:
        """Notify KIconLoader clients when gdbus is available."""
        executable = self.find_executable("gdbus")
        if not executable:
            return False
        self._run([
            executable,
            "emit",
            "--session",
            "--object-path", "/KIconLoader",
            "--signal", "org.kde.KIconLoader.iconChanged",
            "0",
        ])
        return True

    def _reconfigure_kwin(self) -> None:
        executable = self.find_executable("qdbus6") or self.find_executable("qdbus")
        if not executable:
            raise FileNotFoundError("qdbus6 est indisponible pour reconfigurer KWin")
        self._run([executable, "org.kde.KWin", "/KWin", "reconfigure"])

    @staticmethod
    def _is_leos_icon(value: str | None) -> bool:
        return bool(value and value.startswith("leos-"))

    @staticmethod
    def _is_leos_plasma(value: str | None) -> bool:
        return bool(value and value.startswith("leos-"))

    @staticmethod
    def _is_leos_aurorae(value: str | None) -> bool:
        return bool(value and value.startswith("__aurorae__svg__leos-"))

    def _prior_value(
        self,
        current: str | None,
        previous_state: dict[str, Any],
        field: str,
        currently_leos: bool,
    ) -> str | None:
        if currently_leos:
            if not previous_state:
                raise RuntimeError(
                    "Un thème LEOS est déjà actif mais sa sauvegarde précédente est absente."
                )
            return previous_state[field]
        return current

    def apply_theme(self, theme: str) -> str:
        """Apply an exported two-accent theme after an explicit UI confirmation."""
        if theme not in THEME_PALETTES or not THEME_ID_PATTERN.fullmatch(theme):
            raise ValueError("Identifiant de thème LEOS invalide")
        resources = self.assets.exported_kde_resource_paths_for_theme(theme)
        required = {
            "icon_theme_path",
            "plasma_theme_path",
            "aurorae_theme_path",
        }
        if not required.issubset(resources):
            raise FileNotFoundError(
                "Les trois variantes KDE doivent d'abord être exportées dans le profil utilisateur."
            )
        if not self.find_executable("kwriteconfig6"):
            raise FileNotFoundError("kwriteconfig6 est indisponible")
        if not (self._plasma_executable or self.find_executable("plasma-apply-desktoptheme")):
            raise FileNotFoundError("plasma-apply-desktoptheme est indisponible")
        if not (self.find_executable("qdbus6") or self.find_executable("qdbus")):
            raise FileNotFoundError("qdbus6 est indisponible pour reconfigurer KWin")

        current_icons = _read_ini_value(self.kdeglobals, "Icons", "Theme")
        current_plasma = self.plasma_style.current_style()
        current_aurorae_library = _read_ini_value(
            self.kwinrc, "org.kde.kdecoration2", "library"
        )
        current_aurorae_theme = _read_ini_value(
            self.kwinrc, "org.kde.kdecoration2", "theme"
        )
        if current_plasma is None:
            raise RuntimeError(
                "Le Plasma Style actif ne peut pas être identifié ; aucun réglage n'a été modifié."
            )

        previous_state = self._state()
        previous_icons = self._prior_value(
            current_icons, previous_state, "previous_icons",
            self._is_leos_icon(current_icons),
        )
        previous_plasma = self._prior_value(
            current_plasma, previous_state, "previous_plasma",
            self._is_leos_plasma(current_plasma),
        )
        previous_aurorae_library = self._prior_value(
            current_aurorae_library, previous_state, "previous_aurorae_library",
            self._is_leos_aurorae(current_aurorae_theme),
        )
        previous_aurorae_theme = self._prior_value(
            current_aurorae_theme, previous_state, "previous_aurorae_theme",
            self._is_leos_aurorae(current_aurorae_theme),
        )
        if previous_plasma is None:
            raise RuntimeError("Le Plasma Style précédent est inconnu ; aucun changement n'a été effectué.")

        package_id = f"leos-{theme}"
        aurorae_id = f"__aurorae__svg__{package_id}"
        state = {
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "theme": theme,
            "previous_icons": previous_icons,
            "previous_plasma": previous_plasma,
            "previous_aurorae_library": previous_aurorae_library,
            "previous_aurorae_theme": previous_aurorae_theme,
            "last_icons": package_id,
            "last_plasma": package_id,
            "last_aurorae_library": AURORAE_LIBRARY,
            "last_aurorae_theme": aurorae_id,
            "apply_pending": True,
            "restore_icons_done": False,
            "restore_plasma_done": False,
            "restore_aurorae_done": False,
        }
        self._write_state(state)

        completed: list[str] = []
        try:
            completed.append("icons")
            self._write_key(self.kdeglobals, "Icons", "Theme", package_id)

            completed.append("plasma")
            self.plasma_style.apply_style(package_id)

            completed.append("aurorae")
            self._write_key(
                self.kwinrc, "org.kde.kdecoration2", "library", AURORAE_LIBRARY
            )
            self._write_key(
                self.kwinrc, "org.kde.kdecoration2", "theme", aurorae_id
            )
            self._reconfigure_kwin()
            try:
                icons_refreshed = self._refresh_icons()
            except (FileNotFoundError, OSError, RuntimeError, ValueError):
                icons_refreshed = False

            state["apply_pending"] = False
            self._write_state(state)
        except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
            rollback_errors: list[str] = []
            if "aurorae" in completed:
                try:
                    self._write_key(
                        self.kwinrc, "org.kde.kdecoration2", "library",
                        previous_aurorae_library,
                    )
                    self._write_key(
                        self.kwinrc, "org.kde.kdecoration2", "theme",
                        previous_aurorae_theme,
                    )
                    self._reconfigure_kwin()
                except (FileNotFoundError, OSError, RuntimeError, ValueError):
                    rollback_errors.append("Aurorae")
            if "plasma" in completed and self.plasma_style.can_restore():
                try:
                    self.plasma_style.restore_previous_style()
                except (FileNotFoundError, OSError, RuntimeError, ValueError):
                    rollback_errors.append("Plasma")
            if "icons" in completed:
                try:
                    self._write_key(self.kdeglobals, "Icons", "Theme", previous_icons)
                    self._refresh_icons()
                except (FileNotFoundError, OSError, RuntimeError, ValueError):
                    rollback_errors.append("icônes")
            if not rollback_errors:
                self.state_file.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Application du thème KDE refusée ; les réglages précédents ont été rétablis : {error}"
                ) from error
            raise RuntimeError(
                "L'application a échoué et le retour arrière est incomplet pour : "
                + ", ".join(rollback_errors)
                + ". La sauvegarde LEOS est conservée."
            ) from error

        if icons_refreshed:
            return f"Thème KDE LEOS « {theme} » appliqué aux icônes, à Plasma et aux décorations."
        return (
            f"Thème KDE LEOS « {theme} » appliqué. La session peut devoir être relancée "
            "pour actualiser les icônes de toutes les applications."
        )

    def restore_previous_theme(self) -> str:
        """Restore only values that still match LEOS' last applied settings."""
        state = self._state()
        if not state:
            raise FileNotFoundError("Aucune sauvegarde du thème KDE LEOS n'est disponible.")

        restored: list[str] = []
        preserved: list[str] = []

        if not state["restore_icons_done"]:
            current_icons = _read_ini_value(self.kdeglobals, "Icons", "Theme")
            if current_icons == state["last_icons"]:
                self._write_key(
                    self.kdeglobals, "Icons", "Theme", state["previous_icons"]
                )
                try:
                    self._refresh_icons()
                except (FileNotFoundError, OSError, RuntimeError, ValueError):
                    # The config value is restored; a session restart can reload icons.
                    pass
                restored.append("icônes")
            else:
                preserved.append("icônes modifiées depuis l'application LEOS")
            state["restore_icons_done"] = True
            self._write_state(state)

        if not state["restore_plasma_done"]:
            current_plasma = self.plasma_style.current_style()
            if current_plasma == state["last_plasma"]:
                self.plasma_style.restore_previous_style()
                restored.append("Plasma")
            else:
                preserved.append("style Plasma modifié depuis l'application LEOS")
            state["restore_plasma_done"] = True
            self._write_state(state)

        if not state["restore_aurorae_done"]:
            current_aurorae_library = _read_ini_value(
                self.kwinrc, "org.kde.kdecoration2", "library"
            )
            current_aurorae_theme = _read_ini_value(
                self.kwinrc, "org.kde.kdecoration2", "theme"
            )
            if (
                current_aurorae_library == state["last_aurorae_library"]
                and current_aurorae_theme == state["last_aurorae_theme"]
            ):
                self._write_key(
                    self.kwinrc, "org.kde.kdecoration2", "library",
                    state["previous_aurorae_library"],
                )
                self._write_key(
                    self.kwinrc, "org.kde.kdecoration2", "theme",
                    state["previous_aurorae_theme"],
                )
                self._reconfigure_kwin()
                restored.append("Aurorae")
            else:
                preserved.append("décoration modifiée depuis l'application LEOS")
            state["restore_aurorae_done"] = True
            self._write_state(state)

        if self.state_file.is_symlink():
            raise ValueError("Le fichier de sauvegarde KDE est un lien symbolique")
        self.state_file.unlink(missing_ok=True)
        if preserved:
            return (
                "Retour arrière effectué pour : "
                + ", ".join(restored)
                + ". Réglages conservés car modifiés manuellement : "
                + ", ".join(preserved)
                + "."
            )
        return "Thème KDE précédent restauré pour les icônes, Plasma et Aurorae."
