"""Unified game library model with initial Steam manifest discovery.

Other launchers will be added through provider modules after their current
Linux data formats have been tested against real installations.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import tempfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt, Slot
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QProcess


class GameLibraryModel(QAbstractListModel):
    TitleRole = int(Qt.ItemDataRole.UserRole) + 1
    PlatformRole = TitleRole + 1
    SourceRole = TitleRole + 2
    AppIdRole = TitleRole + 3

    def __init__(self) -> None:
        super().__init__()
        data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        self._manual_file = data_home / "leos" / "library.json"
        self._games: list[dict[str, Any]] = []
        self.refresh()

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            self.TitleRole: QByteArray(b"title"),
            self.PlatformRole: QByteArray(b"platform"),
            self.SourceRole: QByteArray(b"source"),
            self.AppIdRole: QByteArray(b"appId"),
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._games)

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._games):
            return None
        game = self._games[index.row()]
        mapping = {
            self.TitleRole: "title",
            self.PlatformRole: "platform",
            self.SourceRole: "source",
            self.AppIdRole: "app_id",
            int(Qt.ItemDataRole.DisplayRole): "title",
        }
        key = mapping.get(role)
        return game.get(key) if key else None

    def _steam_directories(self) -> list[Path]:
        home = Path.home()
        candidates = [
            home / ".local/share/Steam/steamapps",
            home / ".steam/steam/steamapps",
            home / ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps",
        ]
        return [path for path in candidates if path.is_dir()]

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

    def refresh(self) -> None:
        discovered: dict[str, dict[str, Any]] = {}
        for directory in self._steam_directories():
            for manifest in directory.glob("appmanifest_*.acf"):
                game = self._read_steam_manifest(manifest)
                if game:
                    discovered[game["id"]] = game
        for game in self._load_manual_games():
            discovered.setdefault(game["id"], game)

        self.beginResetModel()
        self._games = sorted(discovered.values(), key=lambda item: item["title"].casefold())
        self.endResetModel()

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
    def launchGame(self, row: int) -> bool:
        if not 0 <= row < len(self._games):
            return False
        launch = self._games[row].get("launch", [])
        if not launch:
            return False

        target = launch[0]
        if "://" in target:
            return QDesktopServices.openUrl(QUrl(target))
        return QProcess.startDetached(target, launch[1:])
