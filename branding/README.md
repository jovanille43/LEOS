# LEOS — Branding

Ce dossier regroupe les ressources visuelles et sonores officielles de LEOS.

## Identité officielle

- **Desktop Mode :** emblème officiel avec le lion seul.
- **Gaming Mode :** emblème officiel avec le lion tenant/croquant une manette.
- **Style :** lion métallique, éclairages cyan et magenta, typographie LEOS et fond noir.

L'image comparative des deux emblèmes est une référence interne ; elle ne doit jamais devenir le logo principal d'un écran.

## Organisation

- `desktop-logo.png` — emblème Desktop.
- `gaming-logo.png` — emblème Gaming.
- `reference-comparison.png` — comparaison interne uniquement.
- `animations/` — animations d'entrée des deux modes.
- `sounds/` — signatures sonores et effets LEOS.
- `wallpapers/` — fonds d'écran Desktop et Gaming.
- `icons/` — icônes et éléments graphiques.

Les noms de fichiers, usages, contraintes de fidélité et règles de packaging sont définis dans [ASSET_MANIFEST.md](ASSET_MANIFEST.md).

## Règles

- Ne pas remplacer les emblèmes officiels par des lions génériques.
- Conserver les couleurs, proportions et détails des références originales.
- Utiliser le lion seul pour Desktop et le lion avec manette pour Gaming.
- Ne pas afficher l'image comparative comme emblème d'un mode.
- Les animations et sons doivent pouvoir être désactivés dans les paramètres.
- Préserver les fichiers originaux ; toute optimisation doit produire une copie.

## État

Les chemins d'intégration sont définis, mais les fichiers binaires des emblèmes séparés, des animations et des signatures sonores ne sont pas encore présents dans le dépôt GitHub. Leur intégration ne sera déclarée terminée qu'après vérification des fichiers et test dans une session Bazzite réelle.
