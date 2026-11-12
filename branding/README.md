# LEOS — Branding

Ce dossier regroupe les ressources visuelles et sonores officielles de LEOS.

## Identité officielle

- **Desktop Mode :** emblème officiel avec le lion seul.
- **Gaming Mode :** emblème officiel avec le lion tenant/croquant une manette.
- **Style :** lion métallique, éclairages cyan et magenta, typographie LEOS et fond noir.

L'image comparative des deux emblèmes est une référence interne ; elle ne doit jamais devenir le logo principal d'un écran.

## Organisation

- `desktop-logo.jpeg` — emblème Desktop.
- `gaming-logo.jpeg` — emblème Gaming.
- `reference-comparison.jpeg` — comparaison interne uniquement.
- `animations/` — animations d'entrée des deux modes et variante Gaming de référence.
- Les signatures sonores sont intégrées aux pistes AAC des vidéos MP4 officielles ; aucun dossier `sounds/` séparé n'est requis.
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

Les fichiers sources des emblèmes et des trois animations ont été reçus et identifiés le 12 novembre 2026. Leur correspondance, leurs empreintes et les chemins canoniques prévus sont consignés dans `ASSET_MANIFEST.md`. Les binaires canoniques ne sont pas encore présents dans le dépôt GitHub. Leur intégration ne sera déclarée terminée qu'après vérification des fichiers et test dans une session Bazzite réelle.
