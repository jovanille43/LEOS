"""Safe parsing of Steam appmanifest metadata."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def read_steam_manifest(path: Path) -> dict[str, Any] | None:
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
