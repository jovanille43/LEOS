"""Unified game library with Steam discovery and local categories."""

from __future__ import annotations

import json
import os
import re
import shlex
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
        return {
            "id": f"steam:{app_id}",
            "title": name,
            "platform": "PC",
            "source": "Steam",
            "app_id": app_id,
            "launch": [f"steam://rungameid/{app_id}"],
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
                game["artwork"] = ""
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

    @Slot(int, result=bool)
    def launchGame(self, row: int, mango_hud: bool = False) -> bool:
        if not 0 <= row < len(self._visible_games):
            return False
        game = self._visible_games[row]
        launch = game.get("launch", [])
        if not launch:
            return False

        command = build_launch_command(launch, bool(mango_hud))
        target = command[0]
        if "://" in target:
            launched = QDesktopServices.openUrl(QUrl(target))
        else:
            if target.startswith("~/"):
                target = str(Path(target).expanduser())
            process = QProcess()
            process.setProgram(target)
            process.setArguments(command[1:])
            launched = process.startDetached()
        if launched:
            self._record_recent(str(game["id"]))
        return bool(launched)
