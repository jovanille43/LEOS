"""Safe, read-only preview of regenerable cache and trash contents."""

from __future__ import annotations

from pathlib import Path


def _directory_summary(path: Path) -> dict[str, object]:
    if not path.exists() or path.is_symlink() or not path.is_dir():
        return {
            "available": False,
            "path": str(path),
            "files": 0,
            "bytes": 0,
            "size": "Non disponible",
        }
    total_bytes = 0
    file_count = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            total_bytes += entry.stat(follow_symlinks=False).st_size
                            file_count += 1
                    except OSError:
                        continue
        except OSError:
            continue
    gib = 1024 ** 3
    if total_bytes >= gib:
        size = f"{total_bytes / gib:.2f} Gio"
    elif total_bytes >= 1024 ** 2:
        size = f"{total_bytes / (1024 ** 2):.1f} Mio"
    elif total_bytes >= 1024:
        size = f"{total_bytes / 1024:.1f} Kio"
    else:
        size = f"{total_bytes} octet(s)"
    return {
        "available": True,
        "path": str(path),
        "files": file_count,
        "bytes": total_bytes,
        "size": size,
    }


def collect_cleanup_preview(home: Path | None = None) -> dict[str, object]:
    """Inspect only two explicitly safe locations; never remove or alter files."""
    root = home or Path.home()
    thumbnail_cache = root / ".cache" / "thumbnails"
    trash_files = root / ".local" / "share" / "Trash" / "files"
    thumbnails = _directory_summary(thumbnail_cache)
    trash = _directory_summary(trash_files)
    total = int(thumbnails["bytes"]) + int(trash["bytes"])
    gib = 1024 ** 3
    if total >= gib:
        total_size = f"{total / gib:.2f} Gio"
    elif total >= 1024 ** 2:
        total_size = f"{total / (1024 ** 2):.1f} Mio"
    elif total >= 1024:
        total_size = f"{total / 1024:.1f} Kio"
    else:
        total_size = f"{total} octet(s)"
    return {
        "thumbnails": thumbnails,
        "trash": trash,
        "totalBytes": total,
        "totalSize": total_size,
        "note": "Aucun fichier n’a été modifié. Seuls les caches de miniatures et le contenu de la corbeille sont inspectés.",
    }
