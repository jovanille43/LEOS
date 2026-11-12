"""Safe expansion of freedesktop Desktop Entry Exec field codes."""

from __future__ import annotations

import shlex
from pathlib import Path


_FILE_CODES_WITHOUT_INPUT = frozenset({"%f", "%F", "%u", "%U"})
_DEPRECATED_CODES = frozenset({"%d", "%D", "%n", "%N", "%v", "%m"})
MAX_EXEC_FIELD_LENGTH = 8192
MAX_EXEC_ARGUMENTS = 128
MAX_EXEC_ARGUMENT_LENGTH = 4096


def parse_desktop_exec(
    command: str,
    *,
    name: str = "",
    icon: str = "",
    desktop_file: str = "",
) -> list[str]:
    """Return argv for a .desktop Exec line, without evaluating shell syntax.

    File/URL placeholders are omitted because the LEOS menu launches an
    application without an associated document. Metadata codes are expanded
    from the desktop entry; malformed or unknown percent codes are rejected.
    """
    if not isinstance(command, str) or not command.strip():
        return []
    if len(command) > MAX_EXEC_FIELD_LENGTH or any(
        (ord(char) < 32 and char != "\t") or ord(char) == 127
        for char in command
    ):
        raise ValueError("Desktop Exec field contains invalid or excessive data")
    for metadata in (name, icon, desktop_file):
        if not isinstance(metadata, str) or len(metadata) > MAX_EXEC_ARGUMENT_LENGTH:
            raise ValueError("Desktop Exec metadata is invalid or too long")
        if any(ord(char) < 32 or ord(char) == 127 for char in metadata):
            raise ValueError("Desktop Exec metadata contains control characters")

    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        raise ValueError("Invalid desktop Exec quoting") from exc

    if not tokens:
        return []
    if len(tokens) > MAX_EXEC_ARGUMENTS or any(
        len(token) > MAX_EXEC_ARGUMENT_LENGTH for token in tokens
    ):
        raise ValueError("Desktop Exec field contains too many or oversized arguments")

    file_code_count = sum(token in _FILE_CODES_WITHOUT_INPUT for token in tokens)
    if file_code_count > 1:
        raise ValueError("Only one file or URL field code is permitted")
    if tokens[0] in (_FILE_CODES_WITHOUT_INPUT | _DEPRECATED_CODES | {"%i", "%c", "%k"}):
        raise ValueError("The executable cannot be a desktop Exec field code")

    argv: list[str] = []
    for token in tokens:
        if token in _FILE_CODES_WITHOUT_INPUT or token in _DEPRECATED_CODES:
            continue
        if token == "%i":
            if icon:
                argv.extend(("--icon", icon))
            continue
        if token == "%c":
            if name:
                argv.append(name)
            continue
        if token == "%k":
            if desktop_file:
                argv.append(desktop_file)
            continue

        if "%" in token.replace("%%", ""):
            raise ValueError("Unsupported or misplaced desktop Exec field code")
        argv.append(token.replace("%%", "%"))

    return argv



def resolve_desktop_working_directory(value: str, home: Path | None = None) -> str:
    """Resolve a Desktop Entry Path, rejecting relative or unavailable directories."""
    if not isinstance(value, str) or not value.strip():
        return str((home or Path.home()).resolve())
    candidate = Path(value.strip()).expanduser()
    if not candidate.is_absolute():
        raise ValueError("Desktop Entry Path must be absolute")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("Desktop Entry working directory is unavailable") from exc
    if not resolved.is_dir():
        raise ValueError("Desktop Entry Path is not a directory")
    return str(resolved)
