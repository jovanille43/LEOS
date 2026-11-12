"""Unified game library with Steam discovery and local categories."""

from __future__ import annotations

import json
from itertools import islice
import os
import re
import shutil
from pathlib import Path
from typing import Any

from leos_core.paths import config_home as xdg_config_home, data_home as xdg_data_home

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QProcess

from .library_state import (
    CATEGORIES, filter_games, normalize_display_title, title_identity_key,
    duplicate_title_metadata, upsert_manual_game, read_bounded_json, read_bounded_text,
    MAX_LIBRARY_STATE_FILE_BYTES, MAX_MANUAL_GAMES, MAX_MANUAL_TITLE_LENGTH,
    MAX_MANUAL_PLATFORM_LENGTH, MAX_MANUAL_ARGUMENTS, MAX_MANUAL_ARGUMENT_LENGTH,
    validate_manual_game_input, write_bounded_json,
)
from .steam_artwork import find_steam_artwork
from .steam_manifest import read_steam_manifest
from .heroic import load_heroic_games
from .lutris import find_lutris_artwork, load_lutris_games
from .retroarch import (
    RETROARCH_FLATPAK_ID, find_retroarch_playlist_directories,
    find_retroarch_thumbnail_directories, load_retroarch_games,
)
from .mangohud import build_launch_command
from .install_state import installation_status


MAX_STEAM_MANIFESTS_PER_LIBRARY = 20_000
MAX_RETROARCH_PLAYLISTS_PER_DIRECTORY = 2_000


class GameLibraryModel(QAbstractListModel):
    TitleRole = int(Qt.ItemDataRole.UserRole) + 1
    PlatformRole = TitleRole + 1
    SourceRole = TitleRole + 2
    AppIdRole = TitleRole + 3
    FavoriteRole = TitleRole + 4
    ArtworkRole = TitleRole + 5

    def __init__(self) -> None:
        super().__init__()
        data_home = xdg_data_home()
        data_dir = data_home / "leos"
        self._manual_file = data_dir / "library.json"
        self._favorites_file = data_dir / "favorites.json"
        self._recent_file = data_dir / "recent.json"
        self._games: list[dict[str, Any]] = []
        self._duplicate_metadata: dict[str, dict[str, Any]] = {}
        self._visible_games: list[dict[str, Any]] = []
        self._favorites: set[str] = set()
        self._recent: list[str] = []
        self._category = "Accueil"
        self._search_query = ""
        self._last_launch_status = "Sélectionne un jeu à lancer."
        self.refresh()

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            self.TitleRole: QByteArray(b"title"),
            self.PlatformRole: QByteArray(b"platform"),
            self.SourceRole: QByteArray(b"source"),
            self.AppIdRole: QByteArray(b"appId"),
            self.FavoriteRole: QByteArray(b"favorite"),
            self.ArtworkRole: QByteArray(b"artwork"),
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible_games)

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._visible_games):
            return None
        game = self._visible_games[index.row()]
        mapping = {
            self.TitleRole: "title",
            self.PlatformRole: "platform",
            self.SourceRole: "source",
            self.AppIdRole: "app_id",
            int(Qt.ItemDataRole.DisplayRole): "title",
        }
        if role == self.FavoriteRole:
            return game["id"] in self._favorites
        if role == self.ArtworkRole:
            return str(game.get("artwork", ""))
        key = mapping.get(role)
        return game.get(key) if key else None

    @staticmethod
    def _flatpak_app_available(app_id: str) -> bool:
        data_home = xdg_data_home()
        roots = [data_home / "flatpak" / "app", Path("/var/lib/flatpak/app")]
        return any((root / app_id).is_dir() for root in roots)

    def launcherStatuses(self) -> list[str]:
        launchers = [
            ("STEAM", bool(shutil.which("steam"))
             or self._flatpak_app_available("com.valvesoftware.Steam")),
            ("HEROIC", bool(shutil.which("heroic"))
             or self._flatpak_app_available("com.heroicgameslauncher.hgl")),
            ("LUTRIS", bool(shutil.which("lutris"))
             or self._flatpak_app_available("net.lutris.Lutris")),
            ("RETROARCH", bool(shutil.which("retroarch"))
             or (bool(shutil.which("flatpak"))
                 and self._flatpak_app_available(RETROARCH_FLATPAK_ID))),
        ]
        return [
            f"{name} · {'DISPONIBLE' if available else 'NON DÉTECTÉ'}"
            for name, available in launchers
        ]
    def _steam_roots(self) -> list[Path]:
        home = Path.home()
        candidates = [
            home / ".local/share/Steam",
            home / ".steam/steam",
            home / ".steam/root",
            home / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
        ]
        roots: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            if not candidate.is_dir():
                continue
            resolved = candidate.resolve()
            key = str(resolved)
            if key not in seen:
                seen.add(key)
                roots.append(resolved)
        return roots

    def _steam_directories(self) -> list[Path]:
        directories: list[Path] = []
        seen: set[str] = set()
        for root in self._steam_roots():
            candidates = [root / "steamapps"]
            library_file = root / "steamapps" / "libraryfolders.vdf"
            text = read_bounded_text(library_file) or ""
            for library_path in re.findall(r'"path"\s+"([^"]+)"', text):
                candidates.append(Path(library_path).expanduser() / "steamapps")
            for candidate in candidates:
                if not candidate.is_dir():
                    continue
                resolved = candidate.resolve()
                key = str(resolved)
                if key not in seen:
                    seen.add(key)
                    directories.append(resolved)
        return directories

    def _steam_artwork(self, app_id: str, steamapps_dir: Path) -> str:
        cache_dirs = [
            steamapps_dir.parent / "appcache" / "librarycache",
            *(
                root / "appcache" / "librarycache"
                for root in self._steam_roots()
            ),
        ]
        seen: set[str] = set()
        for cache_dir in cache_dirs:
            key = str(cache_dir)
            if key in seen:
                continue
            seen.add(key)
            artwork = find_steam_artwork(cache_dir, app_id)
            if artwork:
                return artwork.as_uri()
        return ""

    def _lutris_databases(self) -> list[Path]:
        home = Path.home()
        data_home = xdg_data_home()
        candidates = [
            data_home / "lutris/pga.db",
            home / ".local/share/lutris/pga.db",
            home / ".var/app/net.lutris.Lutris/data/lutris/pga.db",
        ]
        found: list[Path] = []
        seen: set[str] = set()
        for path in candidates:
            if path.is_file():
                resolved = path.resolve()
                key = str(resolved)
                if key not in seen:
                    seen.add(key)
                    found.append(resolved)
        return found

    def _heroic_installed_files(self) -> list[tuple[Path, str]]:
        home = Path.home()
        config_roots = [
            xdg_config_home() / "heroic",
            home / ".var/app/com.heroicgameslauncher.hgl/config/heroic",
        ]
        candidates: list[tuple[Path, str]] = []
        seen: set[str] = set()
        for root in config_roots:
            if not root.is_dir():
                continue
            runner_files = {
                "legendary": (
                    root / "legendaryConfig/legendary/installed.json",
                    root / "legendary/installed.json",
                ),
                "gog": (root / "gog_store/installed.json",),
                "nile": (
                    root / "nile_store/installed.json",
                    root / "nile_config/installed.json",
                ),
            }
            for runner, paths in runner_files.items():
                for path in paths:
                    key = str(path)
                    if path.is_file() and key not in seen:
                        seen.add(key)
                        candidates.append((path, runner))
        return candidates

    def _retroarch_playlist_directories(self) -> list[Path]:
        return find_retroarch_playlist_directories(
            xdg_config_home=xdg_config_home()
        )

    def _load_manual_games(self) -> list[dict[str, Any]]:
        raw = read_bounded_json(self._manual_file)
        if not isinstance(raw, list):
            return []
        valid: list[dict[str, Any]] = []
        for item in raw[:MAX_MANUAL_GAMES]:
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            launch = item.get("launch")
            platform = item.get("platform", "PC")
            if (
                isinstance(title, str)
                and 0 < len(title.strip()) <= MAX_MANUAL_TITLE_LENGTH
                and isinstance(platform, str)
                and len(platform.strip()) <= MAX_MANUAL_PLATFORM_LENGTH
                and isinstance(launch, list)
                and 0 < len(launch) <= MAX_MANUAL_ARGUMENTS
                and all(
                    isinstance(part, str) and 0 < len(part) <= 2048 and chr(0) not in part
                    for part in launch
                )
            ):
                candidate_id = item.get("id")
                game_id = (
                    candidate_id
                    if isinstance(candidate_id, str)
                    and candidate_id.startswith("manual:")
                    and len(candidate_id) <= 512
                    else f"manual:{title_identity_key(title)}"
                )
                valid.append({
                    "id": game_id,
                    "title": title.strip(),
                    "platform": platform.strip() or "PC",
                    "source": "Ajout manuel",
                    "app_id": "",
                    "launch": launch,
                })
        return valid

    @staticmethod
    def _read_id_list(path: Path) -> list[str]:
        raw = read_bounded_json(path)
        if not isinstance(raw, list):
            return []
        return list(dict.fromkeys(
            item.strip() for item in raw[:5000]
            if isinstance(item, str) and 0 < len(item.strip()) <= 512
        ))

    @staticmethod
    def _write_id_list(path: Path, values: list[str]) -> None:
        if len(values) > 5000 or any(
            not isinstance(item, str) or not item or len(item) > 512 or chr(0) in item
            for item in values
        ):
            raise ValueError("Invalid game library state identifiers")
        write_bounded_json(path, values)

    def refresh(self) -> None:
        discovered: dict[str, dict[str, Any]] = {}
        # Each provider is isolated: a damaged or temporarily unavailable
        # catalogue must not prevent the remaining sources from loading.
        try:
            steam_directories = self._steam_directories()
        except OSError:
            steam_directories = []
        for directory in steam_directories:
            try:
                manifests = list(islice(directory.glob("appmanifest_*.acf"), MAX_STEAM_MANIFESTS_PER_LIBRARY))
            except OSError:
                continue
            for manifest in manifests:
                game = read_steam_manifest(manifest)
                if game:
                    try:
                        game["artwork"] = self._steam_artwork(game["app_id"], directory)
                    except OSError:
                        game["artwork"] = ""
                    discovered[game["id"]] = game

        try:
            heroic_files = self._heroic_installed_files()
        except OSError:
            heroic_files = []
        for installed_file, runner in heroic_files:
            for game in load_heroic_games(installed_file, runner):
                discovered.setdefault(game["id"], game)

        data_home = xdg_data_home()
        try:
            lutris_databases = self._lutris_databases()
        except OSError:
            lutris_databases = []
        for database in lutris_databases:
            for game in load_lutris_games(database):
                try:
                    artwork = find_lutris_artwork(data_home, str(game.get("slug", "")))
                    game["artwork"] = artwork.as_uri() if artwork else ""
                except OSError:
                    game["artwork"] = ""
                discovered.setdefault(game["id"], game)
        native_retroarch = shutil.which("retroarch")
        flatpak_retroarch = (
            not native_retroarch
            and shutil.which("flatpak") is not None
            and self._flatpak_app_available(RETROARCH_FLATPAK_ID)
        )
        try:
            playlist_directories = self._retroarch_playlist_directories()
        except OSError:
            playlist_directories = []
        try:
            thumbnail_directories = find_retroarch_thumbnail_directories(
                xdg_config_home=xdg_config_home()
            )
        except OSError:
            thumbnail_directories = []
        for directory in playlist_directories:
            try:
                playlists = sorted(islice(directory.glob("*.lpl"), MAX_RETROARCH_PLAYLISTS_PER_DIRECTORY))
            except OSError:
                continue
            for playlist in playlists:
                for game in load_retroarch_games(
                    playlist,
                    native_executable=native_retroarch,
                    flatpak_available=flatpak_retroarch,
                    thumbnail_directories=thumbnail_directories,
                ):
                    discovered.setdefault(game["id"], game)

        for game in self._load_manual_games():
            discovered.setdefault(game["id"], game)

        for game in discovered.values():
            game["title"] = normalize_display_title(str(game.get("title", "")))
        self._games = sorted(discovered.values(), key=lambda item: item["title"].casefold())
        self._duplicate_metadata = duplicate_title_metadata(self._games)
        available_ids = {game["id"] for game in self._games}
        self._favorites = set(self._read_id_list(self._favorites_file)) & available_ids
        self._recent = [
            game_id for game_id in self._read_id_list(self._recent_file)
            if game_id in available_ids
        ][:50]
        self._apply_filter()

    def _apply_filter(self) -> None:
        self.beginResetModel()
        self._visible_games = filter_games(
            self._games,
            self._category,
            self._favorites,
            self._recent,
            self._search_query,
        )
        self.endResetModel()

    @Slot(str)
    def setSearchQuery(self, query: str) -> None:
        query = str(query)[:120]
        if query == self._search_query:
            return
        self._search_query = query
        self._apply_filter()

    @Slot(str)
    def setCategory(self, category: str) -> None:
        if category not in CATEGORIES or category == self._category:
            return
        self._category = category
        self._apply_filter()

    @Slot(int, result=bool)
    def toggleFavorite(self, row: int) -> bool:
        if not 0 <= row < len(self._visible_games):
            return False
        game_id = self._visible_games[row]["id"]
        if game_id in self._favorites:
            self._favorites.remove(game_id)
            is_favorite = False
        else:
            self._favorites.add(game_id)
            is_favorite = True
        try:
            self._write_id_list(self._favorites_file, sorted(self._favorites))
        except (OSError, ValueError):
            if is_favorite:
                self._favorites.discard(game_id)
            else:
                self._favorites.add(game_id)
            return not is_favorite
        self._apply_filter()
        return is_favorite

    def _record_recent(self, game_id: str) -> None:
        self._recent = [game_id] + [
            item for item in self._recent if item != game_id
        ]
        self._recent = self._recent[:50]
        try:
            self._write_id_list(self._recent_file, self._recent)
        except (OSError, ValueError):
            # Keep this session usable even when the user's data directory is
            # temporarily read-only or out of space.
            pass
        # Keep the currently displayed row order stable while a game is launched.
        # The recent-order view is refreshed the next time the category is opened
        # or the user explicitly refreshes the library.

    @Slot(int, result="QVariantMap")
    def gameInfo(self, row: int) -> dict[str, Any]:
        if not 0 <= row < len(self._visible_games):
            return {}
        game = self._visible_games[row]
        return {
            "title": str(game.get("title", "")),
            "platform": str(game.get("platform", "")),
            "source": str(game.get("source", "")),
            "favorite": game["id"] in self._favorites,
            "artwork": str(game.get("artwork", "")),
            "installStatus": (
                installation_status(game)
                if str(game.get("id", "")).startswith(("steam:", "heroic:", "lutris:", "retroarch:"))
                else "Ajout manuel"
            ),
            "appId": str(game.get("app_id", "")),
            "duplicateCount": int(self._duplicate_metadata.get(game["id"], {}).get("count", 1)),
            "duplicateSources": list(self._duplicate_metadata.get(game["id"], {}).get("sources", [])),
        }

    @Slot(str, str, str, result=bool)
    @Slot(str, str, str, result=bool)
    def addManualGame(self, title: str, platform: str, command: str) -> bool:
        validated = validate_manual_game_input(title, platform, command)
        if validated is None:
            return False
        title, platform, launch = validated

        # Never replace a corrupt, oversized, linked, or unsupported file with
        # a partial list just because the loader fell back to an empty result.
        if self._manual_file.is_symlink() or self._manual_file.parent.is_symlink():
            return False
        existing = None
        if self._manual_file.exists():
            existing = read_bounded_json(self._manual_file)
            if not isinstance(existing, list) or len(existing) > MAX_MANUAL_GAMES:
                return False

        games = self._load_manual_games()
        # Do not silently discard malformed records when adding one new entry.
        if existing is not None and len(games) != len(existing):
            return False
        game_id = f"manual:{title_identity_key(title)}"
        identity = title_identity_key(title)
        replacing = any(
            str(game.get("id", "")).startswith("manual:")
            and title_identity_key(str(game.get("title", ""))) == identity
            for game in games
        )
        if len(games) >= MAX_MANUAL_GAMES and not replacing:
            return False
        games = upsert_manual_game(games, {
            "id": game_id,
            "title": title,
            "platform": platform,
            "launch": launch,
        })
        try:
            self._write_manual_games(games)
        except (OSError, ValueError):
            return False
        self.refresh()
        return True

    def _write_manual_games(self, games: list[dict[str, Any]]) -> None:
        if len(games) > MAX_MANUAL_GAMES:
            raise ValueError("Too many manual games")
        write_bounded_json(
            self._manual_file, games, max_bytes=MAX_LIBRARY_STATE_FILE_BYTES
        )


    @property
    def lastLaunchStatus(self) -> str:
        return self._last_launch_status

    @Slot(int, result=bool)
    def launchGame(self, row: int, mango_hud: bool = False) -> bool:
        if not 0 <= row < len(self._visible_games):
            self._last_launch_status = "Sélection de jeu invalide."
            return False
        game = self._visible_games[row]
        launch = game.get("launch", [])
        if not launch or not all(isinstance(part, str) for part in launch):
            self._last_launch_status = "Aucune commande de lancement valide n'est enregistrée."
            return False

        launch_command = list(launch)
        if launch_command[0].startswith("~/"):
            launch_command[0] = str(Path(launch_command[0]).expanduser())
        command = build_launch_command(launch_command, bool(mango_hud))
        target = command[0]
        if not target:
            self._last_launch_status = "La commande de lancement est vide."
            return False

        if "://" in target:
            launched = QDesktopServices.openUrl(QUrl(target))
            self._last_launch_status = (
                "Demande transmise au gestionnaire associé ; le démarrage du jeu n'est pas confirmé."
                if launched else
                "Aucun gestionnaire n'a accepté cette adresse de lancement."
            )
        else:
            executable = (
                shutil.which(target)
                if "/" not in target
                else str(Path(target).expanduser())
                if Path(target).expanduser().is_file()
                and os.access(Path(target).expanduser(), os.X_OK)
                else None
            )
            if not executable:
                self._last_launch_status = "Lanceur ou exécutable introuvable, ou non exécutable."
                return False
            process = QProcess()
            process.setProgram(executable)
            process.setArguments(command[1:])
            launched = process.startDetached()
            self._last_launch_status = (
                "Processus de lancement démarré ; le chargement du jeu n'est pas confirmé."
                if launched else
                "Le système n'a pas réussi à démarrer le processus."
            )
        if launched:
            self._record_recent(str(game["id"]))
        return bool(launched)
