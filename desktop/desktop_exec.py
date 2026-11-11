"""Safe expansion of freedesktop Desktop Entry Exec field codes."""

from __future__ import annotations

import shlex


_FILE_CODES_WITHOUT_INPUT = frozenset({"%f", "%F", "%u", "%U"})
_DEPRECATED_CODES = frozenset({"%d", "%D", "%n", "%N", "%v", "%m"})


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

    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        raise ValueError("Invalid desktop Exec quoting") from exc

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
