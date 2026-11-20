"""Consent-based, reversible activation of the LEOS Desktop profile."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from desktop.dock_favourites import DockFavourites
from desktop.kde_colors import KdeColorSchemeManager
from desktop.layouts import DesktopLayoutStore
from desktop.plasma_adapter import build_panel_management_script
from desktop.plasma_backup import PlasmaBackupManager
from desktop.plasma_inspector import build_layout_plan, inspect_plasma_config
from desktop.plasma_runner import execute_plasma_script
from desktop.plasma_style import PlasmaStyleManager
from leos_core.settings import SettingsStore


APPEARANCE_SETTING = "desktop_appearance_setup"
PENDING = "pending"
APPLIED = "applied"
SKIPPED = "skipped"
DESKTOP_WALLPAPER = Path(__file__).resolve().parents[1] / "branding" / "wallpapers" / "desktop-leos.svg"
DESKTOP_WALLPAPER_URI = "file:///usr/share/leos/branding/wallpapers/desktop-leos.svg"


class DesktopAppearanceSetup:
    """Apply the official Desktop profile only after an explicit user choice.

    The desktop/panel configuration is backed up before Plasma is changed.
    KDE color and Plasma Style managers keep their own verified rollback state.
    Any failed step leaves the first-run state pending so the user can retry.
    """

    def __init__(
        self,
        settings: SettingsStore | None = None,
        *,
        backups: PlasmaBackupManager | None = None,
        colors: KdeColorSchemeManager | None = None,
        style: PlasmaStyleManager | None = None,
        layout: DesktopLayoutStore | None = None,
        favourites: DockFavourites | None = None,
        wallpaper: Path = DESKTOP_WALLPAPER,
        command_lookup: Callable[[str], str | None] | None = None,
        script_executor: Callable[..., tuple[bool, str]] | None = None,
    ) -> None:
        self.settings = settings or SettingsStore()
        self.backups = backups or PlasmaBackupManager()
        self.colors = colors or KdeColorSchemeManager()
        self.style = style or PlasmaStyleManager()
        self.layout = layout or DesktopLayoutStore()
        self.favourites = favourites or DockFavourites()
        self.wallpaper = wallpaper
        self.command_lookup = command_lookup or shutil.which
        self.script_executor = script_executor or execute_plasma_script

    @property
    def status(self) -> str:
        return str(self.settings.get(APPEARANCE_SETTING, PENDING))

    def skip(self) -> str:
        """Remember an explicit decision to keep the existing KDE appearance."""
        current = self.status
        if current != PENDING:
            return current
        self.settings.set(APPEARANCE_SETTING, SKIPPED)
        return SKIPPED

    def _preflight(self) -> dict[str, Any]:
        if self.status != PENDING:
            raise RuntimeError("Le choix d'apparence Desktop a déjà été enregistré.")
        if not self.wallpaper.is_file():
            raise FileNotFoundError("Le fond d'écran officiel Desktop LEOS est absent de l'image.")
        if not self.command_lookup("busctl"):
            raise FileNotFoundError("busctl est absent : Plasma ne peut pas recevoir le profil LEOS.")
        if not self.colors.tool_available():
            raise FileNotFoundError("plasma-apply-colorscheme est indisponible.")
        if not self.style.tool_available() or not self.style.style_installed():
            raise FileNotFoundError("Le Plasma Style LEOS ou son outil d'application est absent.")
        if self.colors.current_scheme() is None:
            raise RuntimeError("Le schéma KDE actuel ne peut pas être identifié ; aucun changement ne sera effectué.")
        if self.style.current_style() is None:
            raise RuntimeError("Le Plasma Style actuel ne peut pas être identifié ; aucun changement ne sera effectué.")

        if not self.favourites.load():
            raise RuntimeError("Les favoris du dock LEOS sont invalides ou illisibles ; aucune modification ne sera effectuée.")

        inspection = inspect_plasma_config(self.backups.config_path)
        plan = build_layout_plan(self.layout.get(), inspection)
        if not plan.get("can_apply"):
            reason = plan.get("blocked_reason") or "La disposition Plasma ne peut pas être adaptée sans risque."
            raise RuntimeError(reason)
        return self.layout.get()

    def _rollback(
        self,
        backup_id: str | None,
        *,
        plasma_script_attempted: bool,
    ) -> list[str]:
        warnings: list[str] = []
        if plasma_script_attempted and backup_id:
            try:
                self.backups.restore_backup(backup_id, confirmed=True)
            except (OSError, RuntimeError, ValueError, PermissionError) as error:
                warnings.append(f"la sauvegarde Plasma n'a pas pu être restaurée ({error})")
        if self.style.can_restore():
            try:
                self.style.restore_previous_style()
            except (OSError, RuntimeError, ValueError, FileNotFoundError) as error:
                warnings.append(f"le style Plasma précédent n'a pas pu être restauré ({error})")
        if self.colors.can_restore():
            try:
                self.colors.restore_previous_theme()
            except (OSError, RuntimeError, ValueError, FileNotFoundError) as error:
                warnings.append(f"le schéma de couleurs précédent n'a pas pu être restauré ({error})")
        return warnings

    def apply(self) -> str:
        """Apply LEOS Original, its wallpaper and dock after the UI gave consent."""
        layout = self._preflight()
        backup_id: str | None = None
        plasma_script_attempted = False
        try:
            # The user's panel and wallpaper configuration is preserved first.
            backup_id = self.backups.create_backup()
            self.colors.apply_theme("leos-original")
            self.style.apply_style()

            script = build_panel_management_script(
                layout,
                self.favourites.items(),
                wallpaper_uri=DESKTOP_WALLPAPER_URI,
            )
            plasma_script_attempted = True
            succeeded, message = self.script_executor(script, timeout=30.0)
            if not succeeded:
                raise RuntimeError(message or "Plasma a refusé le profil Desktop LEOS.")

            self.settings.set(APPEARANCE_SETTING, APPLIED)
            return (
                "L'apparence Desktop LEOS est activée : fond officiel, couleurs, "
                "style Plasma et dock inférieur. Une sauvegarde de ta disposition "
                f"précédente est conservée ({backup_id[:8]})."
            )
        except Exception as error:
            rollback_warnings = self._rollback(
                backup_id,
                plasma_script_attempted=plasma_script_attempted,
            )
            detail = f"Activation LEOS interrompue : {error}"
            if rollback_warnings:
                detail += " Attention : " + "; ".join(rollback_warnings) + "."
            else:
                detail += " Les réglages précédents ont été restaurés."
            raise RuntimeError(detail) from error
