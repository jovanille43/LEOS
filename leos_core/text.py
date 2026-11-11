"""Small text-normalization helpers shared across LEOS interfaces."""

from __future__ import annotations

import unicodedata


def normalize_search_text(value: object) -> str:
    """Normalize search text by case, accents and repeated whitespace."""
    if not isinstance(value, str):
        return ""
    collapsed = " ".join(value.split())
    decomposed = unicodedata.normalize("NFKD", collapsed).casefold()
    return "".join(
        character for character in decomposed
        if not unicodedata.combining(character)
    )
