"""Unified game library with Steam discovery and local categories."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import tempfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QProcess

from .library_state import CATEGORIES, filter_games
from .steam_artwork import find_steam_artwork
from .heroic import load_heroic_games
from .lutris import find_lutris_artwork, load_lutris_games
from .mangohud import build_launch_command
from .install_state import installation_status


class GameLibraryModel(QAbstractListModel):
    TitleRole = int(Qt.ItemDataRole.UserRole) + 1
    PlatformRole = TitleRole + 1
    SourceRole = TitleRole + 2
    AppIdRole = TitleRole + 3
    FavoriteRole = TitleRole + 4
    ArtworkRole = TitleRole + 5

    def __init__(self) -> None:
        super().__init__()
        data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        data_dir = data_home / "leos"
        self._manual_file = data_dir / "library.json"
        self._favorites_file = data_dir / "favorites.json"
        self._recent_file = data_dir / "recent.json"
        self._games: list[dict[str, Any]] = []
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
        data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
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
            try:
                text = library_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
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
        data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
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
            home / ".config" / "heroic",
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

    @staticmethod
    def _read_steam_manifest(path: Path) -> dict[str, Any] | None:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        app_id_match = re.search(r'"appid"\s+"(\d+)"', text)
        name_match = re.search(r'"name"\s+"((?:\\.|[^"])*)"', text)
        if not app_id_match or not name_match:
            return None
        name = name_match.group(1).replace(r'\"', '"').replace(r"\\", "\\").strip()
        if not name:
            return None
        app_id = app_id_match.group(1)
        install_dir_match = re.search(r'"installdir"\s+"((?:\\.|[^"])*)"', text)
        install_dir = (
            install_dir_match.group(1).replace(r'\"', '"').replace(r"\\", "\\")
            if install_dir_match else ""
        )
        install_path = (
            str(path.parent / "common" / install_dir)
            if (
                install_dir
                and install_dir not in {".", ".."}
                and Path(install_dir).name == install_dir
                and "/" not in install_dir
                and "\\" not in install_dir
            )
            else ""
        )
        return {
            "id": f"steam:{app_id}",
            "title": name,
            "platform": "PC",
            "source": "Steam",
            "app_id": app_id,
            "launch": [f"steam://rungameid/{app_id}"],
            "install_path": install_path,
        }

    def _load_manual_games(self) -> list[dict[str, Any]]:
        try:
            raw = json.loads(self._manual_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(raw, list):
            return []
        valid: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            launch = item.get("launch")
            if (
                isinstance(title, str)
                and title.strip()
                and isinstance(launch, list)
                and launch
                and all(isinstance(part, str) for part in launch)
            ):
                valid.append({
                    "id": str(item.get("id", f"manual:{title}")),
                    "title": title.strip(),
                    "platform": str(item.get("platform", "PC")),
                    "source": "Ajout manuel",
                    "app_id": "",
                    "launch": launch,
                })
        return valid

    @staticmethod
    def _read_id_list(path: Path) -> list[str]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(raw, list):
            return []
        return list(dict.fromkeys(
            item.strip() for item in raw
            if isinstance(item, str) and item.strip()
        ))

    @staticmethod
    def _write_id_list(path: Path, values: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f"{path.stem}.", suffix=".tmp", dir=path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(values, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

    def refresh(self) -> None:
        discovered: dict[str, dict[str, Any]] = {}
        for directory in self._steam_directories():
            for manifest in directory.glob("appmanifest_*.acf"):
                game = self._read_steam_manifest(manifest)
                if game:
                    game["artwork"] = self._steam_artwork(game["app_id"], directory)
                    discovered[game["id"]] = game
        for installed_file, runner in self._heroic_installed_files():
            for game in load_heroic_games(installed_file, runner):
                discovered.setdefault(game["id"], game)
        data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        for database in self._lutris_databases():
            for game in load_lutris_games(database):
                artwork = find_lutris_artwork(data_home, str(game.get("slug", "")))
                game["artwork"] = artwork.as_uri() if artwork else ""
                discovered.setdefault(game["id"], game)
        for game in self._load_manual_games():
            discovered.setdefault(game["id"], game)

        self._games = sorted(discovered.values(), key=lambda item: item["title"].casefold())
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
        self._write_id_list(self._favorites_file, sorted(self._favorites))
        self._apply_filter()
        return is_favorite

    def _record_recent(self, game_id: str) -> None:
        self._recent = [game_id] + [
            item for item in self._recent if item != game_id
        ]
        self._recent = self._recent[:50]
        self._write_id_list(self._recent_file, self._recent)
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
                if str(game.get("id", "")).startswith(("steam:", "heroic:", "lutris:"))
                else "Ajout manuel"
            ),
            "appId": str(game.get("app_id", "")),
        }

    @Slot(str, str, str, result=bool)
    def addManualGame(self, title: str, platform: str, command: str) -> bool:
        title = title.strip()
        platform = platform.strip() or "PC"
        if not title or not command.strip():
            return False

        try:
            launch = shlex.split(command, posix=True)
        except ValueError:
            return False
        if not launch:
            return False

        games = self._load_manual_games()
        game_id = f"manual:{title.casefold()}"
        games = [game for game in games if game.get("id") != game_id]
        games.append({
            "id": game_id,
            "title": title,
            "platform": platform,
            "launch": launch,
        })
        self._write_manual_games(games)
        self.refresh()
        return True

    def _write_manual_games(self, games: list[dict[str, Any]]) -> None:
        self._manual_file.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix="library.", suffix=".tmp", dir=self._manual_file.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(games, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, self._manual_file)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

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
