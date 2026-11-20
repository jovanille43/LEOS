"""Consent-based, reversible activation of the LEOS Desktop profile."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from desktop.dock_favourites import DockFavourites
from desktop.branding_assets import build_themed_branding_assets, source_asset_urls
from desktop.kde_colors import KdeColorSchemeManager
from desktop.icon_theme import PlasmaIconThemeManager
from desktop.layouts import DesktopLayoutStore
from desktop.plasma_adapter import build_panel_management_script
from desktop.plasma_backup import PlasmaBackupManager
from desktop.plasma_inspector import build_layout_plan, inspect_plasma_config
from desktop.plasma_runner import execute_plasma_script
from desktop.plasma_style import PlasmaStyleManager
from desktop.themed_plasma_resources import install_themed_plasma_resources
from desktop.visual_chrome import PlasmaVisualChromeManager
from desktop.themes import normalize_color, resolve_appearance_mode
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
        icons: PlasmaIconThemeManager | None = None,
        layout: DesktopLayoutStore | None = None,
        favourites: DockFavourites | None = None,
        wallpaper: Path = DESKTOP_WALLPAPER,
        command_lookup: Callable[[str], str | None] | None = None,
        script_executor: Callable[..., tuple[bool, str]] | None = None,
        branding_asset_builder: Callable[[str, str], dict[str, str]] | None = None,
        plasma_resource_builder: Callable[[str, str], dict[str, str]] | None = None,
        visual_chrome: PlasmaVisualChromeManager | None = None,
    ) -> None:
        self.settings = settings or SettingsStore()
        self.backups = backups or PlasmaBackupManager()
        self.colors = colors or KdeColorSchemeManager()
        self.style = style or PlasmaStyleManager()
        self.icons = icons or PlasmaIconThemeManager()
        self.layout = layout or DesktopLayoutStore()
        self.favourites = favourites or DockFavourites()
        self.wallpaper = wallpaper
        self.command_lookup = command_lookup or shutil.which
        self.script_executor = script_executor or execute_plasma_script
        self.branding_asset_builder = branding_asset_builder or build_themed_branding_assets
        self.plasma_resource_builder = plasma_resource_builder or install_themed_plasma_resources
        self.visual_chrome = visual_chrome or PlasmaVisualChromeManager()

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
        if not self.settings.get("theme_colors_configured", False):
            raise RuntimeError("Choisis et enregistre les deux couleurs A et B avant d’activer l’apparence LEOS.")
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
        if not self.icons.tool_available() or not self.icons.theme_installed():
            raise FileNotFoundError("Le thème d'icônes LEOS ou plasma-changeicons est indisponible.")
        if self.icons.current_theme() is None:
            raise RuntimeError("Le thème d'icônes KDE actuel ne peut pas être identifié ; aucun changement ne sera effectué.")
        if not self.visual_chrome.tool_available():
            raise FileNotFoundError("Les outils KDE de configuration de l'écran de chargement et du curseur sont indisponibles.")
        if not self.visual_chrome.splash_theme_installed():
            raise FileNotFoundError("L'écran de chargement Plasma LEOS est absent de l'image.")
        if not self.visual_chrome.aurorae_theme_installed("leos"):
            raise FileNotFoundError("Le décor de fenêtres Aurorae LEOS est absent de l'image.")

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
        if self.visual_chrome.can_restore():
            try:
                self.visual_chrome.restore_previous()
            except (OSError, RuntimeError, ValueError, FileNotFoundError) as error:
                warnings.append(f"l'écran de chargement, le curseur ou le décor de fenêtres précédent n'a pas pu être restauré ({error})")
        if self.icons.can_restore():
            try:
                self.icons.restore_previous_theme()
            except (OSError, RuntimeError, ValueError, FileNotFoundError) as error:
                warnings.append(f"le thème d'icônes précédent n'a pas pu être restauré ({error})")
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
        """Apply the user-selected A/B identity and reversible Desktop profile."""
        layout = self._preflight()
        color_a, color_b, appearance_mode = self.settings.snapshot(
            ("theme_color_a", "theme_color_b", "appearance_mode")
        )
        color_a = normalize_color(str(color_a))
        color_b = normalize_color(str(color_b))
        resolved_appearance = resolve_appearance_mode(str(appearance_mode or "dark"))
        backup_id: str | None = None
        plasma_script_attempted = False
        try:
            # Build only user-scoped asset variants; official source files remain immutable.
            assets = self.branding_asset_builder(color_a, color_b)
            wallpaper_uri = assets.get("desktopWallpaperUrl")
            original_wallpaper_uri = source_asset_urls()["desktopWallpaperUrl"]
            if not wallpaper_uri or wallpaper_uri == original_wallpaper_uri:
                raise RuntimeError(
                    "Le fond personnalisé A/B n’a pas pu être généré ; le bureau existant est conservé."
                )

            # Plasma loads themes from XDG_DATA_HOME, so install a uniquely named
            # user-scoped variant generated from the same A/B pair.
            plasma_resources = self.plasma_resource_builder(color_a, color_b)
            plasma_style_id = plasma_resources.get("plasmaStyleId")
            icon_theme_id = plasma_resources.get("iconThemeId")
            aurorae_theme_id = plasma_resources.get("auroraeThemeId")
            if not plasma_style_id or not icon_theme_id or not aurorae_theme_id:
                raise RuntimeError("Les variantes Plasma, icônes et décor de fenêtres personnalisées ne sont pas disponibles.")

            # Preserve the user's panel and wallpaper configuration before changing Plasma.
            backup_id = self.backups.create_backup()
            self.colors.apply_custom_theme(color_a, color_b, resolved_appearance)
            self.style.apply_style(plasma_style_id)
            self.icons.apply_theme(icon_theme_id)
            self.visual_chrome.apply(
                "org.leos.desktop", icon_theme_id, aurorae_theme_id, wallpaper_uri
            )

            script = build_panel_management_script(
                layout,
                self.favourites.items(),
                wallpaper_uri=wallpaper_uri,
            )
            plasma_script_attempted = True
            succeeded, message = self.script_executor(script, timeout=30.0)
            if not succeeded:
                raise RuntimeError(message or "Plasma a refusé le profil Desktop LEOS.")

            self.settings.set(APPEARANCE_SETTING, APPLIED)
            return (
                "L'apparence Desktop LEOS est activée : fond personnalisé, dégradé A/B, "
                "style Plasma, icônes et curseur LEOS assortis à tes couleurs A/B, plus l'écran de chargement LEOS et le dock inférieur. Une sauvegarde de ta disposition "
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
