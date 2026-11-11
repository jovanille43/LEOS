"""QML image provider backed by the user's active KDE icon theme."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtQuick import QQuickImageProvider


class DesktopIconProvider(QQuickImageProvider):
    """Resolve Desktop Entry icon names without changing the icon theme."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Pixmap)

    def requestPixmap(
        self,
        identifier: str,
        size: QSize,
        requested_size: QSize,
    ) -> QPixmap:
        icon_name = unquote(str(identifier)).strip()
        icon = QIcon()
        if icon_name:
            candidate = Path(icon_name).expanduser()
            if candidate.is_absolute() and candidate.is_file():
                icon = QIcon(str(candidate))
            else:
                icon = QIcon.fromTheme(icon_name)

        if icon.isNull():
            icon = QIcon.fromTheme("application-x-executable")
        if icon.isNull():
            icon = QIcon.fromTheme("application-x-desktop")

        target = QSize(requested_size)
        if not target.isValid() or target.isEmpty():
            target = QSize(64, 64)

        pixmap = icon.pixmap(target)
        if pixmap.isNull():
            pixmap = QPixmap(target)
            pixmap.fill(Qt.GlobalColor.transparent)
        elif pixmap.size() != target:
            pixmap = pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        if size is not None:
            size.setWidth(pixmap.width())
            size.setHeight(pixmap.height())
        return pixmap
