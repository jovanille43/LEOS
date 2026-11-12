"""Validated, bounded loader for the built-in LEOS application catalogue."""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from leos_core.json_utils import json_nesting_within_limit


MAX_CATALOG_BYTES = 256 * 1024
MAX_CATALOG_ITEMS = 128
MAX_CATALOG_FIELD_LENGTH = 2048
APP_ID_RE = re.compile(r"^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+$")

_REQUIRED_FIELDS = frozenset({
    "id", "name", "category", "description", "source",
    "compatibility", "operation_note",
})
_ALLOWED_FIELDS = _REQUIRED_FIELDS | {"bundled"}


def load_catalog(path: Path) -> list[dict[str, Any]]:
    """Load a small trusted catalogue while rejecting unsafe or malformed files."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError("Catalogue inaccessible ou lié symboliquement") from exc

    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Le catalogue n'est pas un fichier régulier")
        if before.st_size <= 0 or before.st_size > MAX_CATALOG_BYTES:
            raise ValueError("Le catalogue dépasse sa limite de taille")
        chunks: list[bytes] = []
        remaining = MAX_CATALOG_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(raw) > MAX_CATALOG_BYTES
            or len(raw) != before.st_size
            or before.st_ino != after.st_ino
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
        ):
            raise ValueError("Le catalogue a changé pendant sa lecture")
    finally:
        os.close(descriptor)

    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("Le catalogue n'est pas encodé en UTF-8") from exc
    if not json_nesting_within_limit(text):
        raise ValueError("La structure JSON du catalogue est invalide ou trop profonde")
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("Le catalogue contient un JSON invalide") from exc

    if not isinstance(payload, list) or not 1 <= len(payload) <= MAX_CATALOG_ITEMS:
        raise ValueError("Le catalogue doit contenir un nombre limité d'applications")
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in payload:
        if not isinstance(item, dict) or not _REQUIRED_FIELDS.issubset(item) or not set(item).issubset(_ALLOWED_FIELDS):
            raise ValueError("Une fiche du catalogue a un schéma invalide")
        for field in _REQUIRED_FIELDS:
            value = item[field]
            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value) > MAX_CATALOG_FIELD_LENGTH
                or any(ord(character) < 32 and character not in "\t\n" for character in value)
            ):
                raise ValueError(f"Champ de catalogue invalide : {field}")
        app_id = item["id"]
        if not APP_ID_RE.fullmatch(app_id) or app_id in seen_ids:
            raise ValueError("Identifiant d'application invalide ou dupliqué")
        if "bundled" in item and type(item["bundled"]) is not bool:
            raise ValueError("Le champ bundled doit être booléen")
        seen_ids.add(app_id)
        items.append(dict(item))
    return items
