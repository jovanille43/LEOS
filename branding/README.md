# LEOS — Branding

Ce dossier contient les ressources visuelles officielles utilisées par LEOS.

## Identité

- **Desktop Mode :** emblème du lion seul.
- **Gaming Mode :** emblème du lion avec manette.
- **Style :** lion métallique, typographie LEOS, fond sombre et dégradé composé de deux couleurs A/B choisies librement.

## Couleurs A/B

- L’utilisateur choisit deux accents indépendants A et B avec le sélecteur natif ou un code HEX `#RRGGBB`.
- Les couleurs peuvent être identiques ou proches ; un contraste faible déclenche un avertissement de lisibilité, sans changer A ni B.
- Les surfaces sombres, les tons neutres et les reflets métalliques restent préservés.
- Les accents présents dans les visuels d'origine sont uniquement des points techniques de transformation ; ils ne sont jamais imposés comme couleurs utilisateur.
- Les variantes de logos, de fonds et, lorsque l’encodeur est disponible, d’introductions sont générées dans le cache privé utilisateur. Les sources officielles restent intactes.

## Organisation

- `desktop-logo.jpeg` — emblème Desktop.
- `gaming-logo.jpeg` — emblème Gaming.
- `reference-comparison.jpeg` — référence interne uniquement.
- `animations/desktop-intro.mov` — entrée Desktop et retour depuis Gaming.
- `animations/gaming-intro.mp4` — animation principale d'entrée Gaming.
- `animations/gaming-roar-reference.mp4` — variante secondaire de référence.
- `wallpapers/desktop-leos.svg` — fond Desktop 4K (3840 × 2160), avec l'emblème officiel référencé depuis `desktop-logo.jpeg` sans modification.
- `wallpapers/gaming-leos.svg` — fond Gaming 4K (3840 × 2160), avec l'emblème officiel référencé depuis `gaming-logo.jpeg` sans modification.
- Le fond Desktop personnalisé est appliqué après consentement explicite et sauvegarde Plasma ; le fond Gaming reste une ressource officielle disponible pour l'interface correspondante.
- `icons/` — icônes et éléments graphiques.

Les pistes audio intégrées aux vidéos sont lues avec Qt Multimedia. Le réglage LEOS des sons permet de les couper sans désactiver les animations ; aucun dossier `sounds/` séparé n'est requis.

La recette BlueBuild copie ce dossier dans `/usr/share/leos/branding/`. Les chemins et l'état de vérification sont détaillés dans [ASSET_MANIFEST.md](ASSET_MANIFEST.md).

## Règles

- Ne pas remplacer les emblèmes officiels par des lions génériques.
- Conserver les couleurs, proportions et détails des références.
- Ne pas afficher l'image comparative comme emblème.
- Préserver les fichiers sources ; toute optimisation doit produire une copie dérivée.
- Tester le décodage vidéo et audio dans une session Bazzite réelle avant publication.

## Identité de démarrage et de connexion

- Plymouth présente l'emblème Desktop officiel sur un fond graphite neutre avant l'ouverture de session. Le watermark PNG est produit à la construction de l'image.
- SDDM présente le logo Desktop officiel, une connexion Qt 6 avec choix de session et la typographie Noto Sans. Les accents A/B personnels ne sont pas imposés avant la connexion.
- Plasma fournit un écran de chargement LEOS post-connexion. Il est activé après le consentement au profil Desktop.
- Le curseur LEOS ajoute une première forme SVG recolorable avec A/B ; les formes non fournies héritent de Breeze pour préserver la compatibilité.

Noto Sans est la famille commune des interfaces de connexion, de démarrage et de chargement. Les emblèmes restent ceux des ressources graphiques officielles.
