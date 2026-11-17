#!/usr/bin/env python3
"""Dérive les emblèmes LEOS transparents à partir des JPEG officiels.

Les JPEG officiels (branding/desktop-logo.jpeg, branding/gaming-logo.jpeg) ont un
fond noir opaque : posés sur un fond d'écran à halos, ils dessinent un rectangle
noir. Ce script produit des copies dérivées en PNG RGBA, sans toucher aux sources.

Modèle « lumière émise » : l'alpha est la luminosité maximale du pixel et la
couleur est dépréniée en conséquence. Composé sur du noir, le résultat redonne
l'emblème d'origine (à FLOOR niveaux près) ; composé sur un fond coloré, le
néon s'ajoute au fond au lieu de le masquer.

Usage (depuis la racine du dépôt, nécessite Pillow et numpy) :
    python3 tools/derive_emblem_alpha.py          # régénère les deux PNG
    python3 tools/derive_emblem_alpha.py --check  # vérifie qu'ils sont à jour
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRANDING = ROOT / "branding"
EMBLEMS = ("desktop", "gaming")
FLOOR = 4  # bruit de compression JPEG sur le noir, ramené à une transparence totale


def derive(source: Path):
    import numpy as np
    from PIL import Image

    rgb = np.asarray(Image.open(source).convert("RGB"), dtype=np.float32)
    rgb = np.clip(rgb - FLOOR, 0.0, None)
    peak = rgb.max(axis=2)
    safe = np.where(peak > 0, peak, 1.0)
    color = rgb * (255.0 / safe)[..., None]
    out = np.dstack([color, peak]).round().clip(0, 255).astype("uint8")
    return Image.fromarray(out, "RGBA")


def target(name: str) -> Path:
    return BRANDING / f"{name}-logo-alpha.png"


def main(argv: list[str]) -> int:
    import numpy as np
    from PIL import Image

    check = "--check" in argv
    status = 0
    for name in EMBLEMS:
        source = BRANDING / f"{name}-logo.jpeg"
        expected = derive(source)
        path = target(name)
        if check:
            if not path.is_file():
                print(f"MANQUANT  {path.relative_to(ROOT)}")
                status = 1
                continue
            current = np.asarray(Image.open(path).convert("RGBA"), dtype=np.int16)
            diff = int(np.abs(current - np.asarray(expected, dtype=np.int16)).max())
            print(f"{'OK' if diff <= 1 else 'ÉCART'}  {path.relative_to(ROOT)} (écart max {diff})")
            status |= int(diff > 1)
        else:
            expected.save(path, optimize=True)
            print(f"écrit  {path.relative_to(ROOT)}")
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
