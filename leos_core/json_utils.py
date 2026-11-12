"Small defensive helpers shared by LEOS JSON-backed stores."

from __future__ import annotations


MAX_JSON_NESTING = 128


def json_nesting_within_limit(payload: str, max_depth: int = MAX_JSON_NESTING) -> bool:
    """Reject excessive container nesting before invoking the JSON decoder.

    Brackets inside JSON strings are ignored. Full syntax validation remains
    the responsibility of json.loads.
    """
    if not isinstance(payload, str) or type(max_depth) is not int or max_depth < 0:
        return False

    depth = 0
    in_string = False
    escaped = False
    for character in payload:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue

        if character == '"' :
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > max_depth:
                return False
        elif character in "]}":
            depth -= 1
            if depth < 0:
                return False

    return not in_string and depth == 0
