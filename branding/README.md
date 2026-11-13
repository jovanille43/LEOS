# LEOS — Branding

Ce dossier contient les ressources visuelles officielles utilisées par LEOS.

## Identité

- **Desktop Mode :** emblème du lion seul.
- **Gaming Mode :** emblème du lion avec manette.
- **Style :** lion métallique, accents cyan et magenta, typographie LEOS et fond noir.

## Organisation

- `desktop-logo.jpeg` — emblème Desktop.
- `gaming-logo.jpeg` — emblème Gaming.
- `desktop-logo-alpha.png` et `gaming-logo-alpha.png` — copies dérivées (PNG transparent) des deux emblèmes ci-dessus, générées par `tools/derive_emblem_alpha.py` ; elles servent aux fonds d'écran pour éviter le rectangle noir du JPEG. Les JPEG restent les sources officielles.
- `reference-comparison.jpeg` — référence interne uniquement.
- `animations/desktop-intro.mov` — entrée Desktop et retour depuis Gaming.
- `animations/gaming-intro.mp4` — animation principale d'entrée Gaming.
- `animations/gaming-roar-reference.mp4` — variante secondaire de référence.
- `wallpapers/desktop-leos.svg` — fond Desktop 4K (3840 × 2160), avec l'emblème officiel référencé via `desktop-logo-alpha.png`, copie dérivée de `desktop-logo.jpeg`.
- `wallpapers/gaming-leos.svg` — fond Gaming 4K (3840 × 2160), avec l'emblème officiel référencé via `gaming-logo-alpha.png`, copie dérivée de `gaming-logo.jpeg`.
- Les deux fonds sont des ressources sélectionnables ; aucun n'est appliqué automatiquement.
- `icons/` — icônes et éléments graphiques.

Les pistes audio intégrées aux vidéos sont lues avec Qt Multimedia. Le réglage LEOS des sons permet de les couper sans désactiver les animations ; aucun dossier `sounds/` séparé n'est requis.

La recette BlueBuild copie ce dossier dans `/usr/share/leos/branding/`. Les chemins et l'état de vérification sont détaillés dans [ASSET_MANIFEST.md](ASSET_MANIFEST.md).

## Règles

- Ne pas remplacer les emblèmes officiels par des lions génériques.
- Conserver les couleurs, proportions et détails des références.
- Ne pas afficher l'image comparative comme emblème.
- Préserver les fichiers sources ; toute optimisation doit produire une copie dérivée.
- Tester le décodage vidéo et audio dans une session Bazzite réelle avant publication.
