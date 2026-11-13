# LEOS — Branding

Ce dossier contient les ressources visuelles officielles utilisées par LEOS.

## Identité

- **Desktop Mode :** emblème du lion seul.
- **Gaming Mode :** emblème du lion avec manette.
- **Style :** lion métallique, dégradé défini par Couleur A et Couleur B, typographie LEOS et fond noir. Cyan/magenta sont les couleurs par défaut historiques.

## Organisation

- `desktop-logo.jpeg` — emblème Desktop.
- `gaming-logo.jpeg` — emblème Gaming.
- `reference-comparison.jpeg` — référence interne uniquement.
- `animations/desktop-intro.mov` — entrée Desktop et retour depuis Gaming.
- `animations/gaming-intro.mp4` — animation principale d'entrée Gaming.
- `animations/gaming-roar-reference.mp4` — variante secondaire de référence.
- `wallpapers/desktop-leos.svg` — fond Desktop 4K (3840 × 2160), avec l'emblème officiel référencé depuis `desktop-logo.jpeg` sans modification.
- `wallpapers/gaming-leos.svg` — fond Gaming 4K (3840 × 2160), avec l'emblème officiel référencé depuis `gaming-logo.jpeg` sans modification.
- Les deux fonds sont des ressources sélectionnables ; aucun n'est appliqué automatiquement.
- `icons/` — icônes et éléments graphiques.

Les JPEG, vidéos et SVG conservent actuellement leurs couleurs intégrées d'origine ; ils ne sont pas encore recolorés automatiquement lorsque l'utilisateur change A/B. Les fichiers sources ne doivent jamais être écrasés : toute adaptation devra produire une variante dérivée et préserver les reflets métalliques ainsi que le dégradé d'origine.

Les pistes audio intégrées aux vidéos sont lues avec Qt Multimedia. Le réglage LEOS des sons permet de les couper sans désactiver les animations ; aucun dossier `sounds/` séparé n'est requis.

La recette BlueBuild copie ce dossier dans `/usr/share/leos/branding/`. Les chemins et l'état de vérification sont détaillés dans [ASSET_MANIFEST.md](ASSET_MANIFEST.md).

## Règles

- Ne pas remplacer les emblèmes officiels par des lions génériques.
- Conserver les couleurs, proportions et détails des références.
- Ne pas afficher l'image comparative comme emblème.
- Préserver les fichiers sources ; toute optimisation doit produire une copie dérivée.
- Tester le décodage vidéo et audio dans une session Bazzite réelle avant publication.
