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

- `desktop-logo.jpeg` et `gaming-logo.jpeg` — sources officielles préservées.
- `desktop-logo.png` et `gaming-logo.png` — variantes transparentes cadrées pour les interfaces.
- `desktop-wallpaper-logo.png` et `gaming-wallpaper-logo.png` — variantes transparentes sur le canevas source 1376 × 768 pour les fonds d’écran.
- Les quatre PNG sont régénérés depuis les JPEG conservés avec `python3 tools/prepare-transparent-branding.py` (Pillow requis).
- `reference-comparison.jpeg` — référence interne uniquement.
- `animations/desktop-intro.mov` — entrée Desktop et retour depuis Gaming.
- `animations/gaming-intro.mp4` — animation principale d'entrée Gaming.
- `animations/gaming-roar-reference.mp4` — variante secondaire de référence.
- `wallpapers/desktop-leos.svg` — fond Desktop 4K (3840 × 2160), avec `desktop-wallpaper-logo.png` transparent sur le canevas source.
- `wallpapers/gaming-leos.svg` — fond Gaming 4K (3840 × 2160), avec `gaming-wallpaper-logo.png` transparent sur le canevas source.
- Le fond Desktop personnalisé est appliqué après consentement explicite et sauvegarde Plasma ; le fond Gaming reste une ressource officielle disponible pour l'interface correspondante.
- `icons/` — icônes et éléments graphiques.

Les pistes audio intégrées aux vidéos sont lues avec Qt Multimedia. Le réglage LEOS des sons permet de les couper sans désactiver les animations ; aucun dossier `sounds/` séparé n'est requis.

La recette BlueBuild copie uniquement les PNG transparents, les deux introductions actives, les fonds SVG et le composant QML partagé dans `/usr/share/leos/branding/`. Les JPEG sources, la comparaison et la vidéo secondaire restent des références du dépôt et ne sont pas installés dans l'image. Les chemins et l'état de vérification sont détaillés dans [ASSET_MANIFEST.md](ASSET_MANIFEST.md).

## Règles

- Ne pas remplacer les emblèmes officiels par des lions génériques.
- Conserver les couleurs, proportions et détails des références.
- Ne pas afficher l'image comparative comme emblème.
- Préserver les fichiers sources ; toute optimisation doit produire une copie dérivée.
- Tester le décodage vidéo et audio dans une session Bazzite réelle avant publication.

## Identité de démarrage et de connexion

- Plymouth présente l'emblème Desktop officiel sur un fond graphite neutre avant l'ouverture de session. Le watermark PNG est produit à la construction de l'image.
- SDDM présente le logo Desktop officiel, une connexion Qt 6 avec choix de session, disposition clavier, horloge et commandes de veille/redémarrage/extinction confirmées. La typographie Noto Sans et la base graphite restent neutres avant le choix A/B.
- Plasma fournit un écran de chargement LEOS post-connexion. Il est activé après le consentement au profil Desktop.
- Le curseur LEOS propose une famille SVG A/B cohérente : flèche, main, texte, attente, progression, viseur, interdit, déplacement et redimensionnements ; les formes rares non fournies héritent de Breeze. Les 11 formes sont générées à la construction dans le dossier cursors_scalable du thème d'icônes.
- Les fenêtres KWin utilisent une variante Aurorae dans l'espace utilisateur : cadres, boutons et état actif/inactif sont recolorés selon A/B, sans modifier les ressources système.
- Le fond du verrouillage KDE utilise aussi le fond Desktop A/B, tandis que la saisie du mot de passe reste celle du greeter natif.

Noto Sans est la famille commune des interfaces de connexion, de démarrage et de chargement. Les emblèmes restent ceux des ressources graphiques officielles.

## Écran de verrouillage

Le profil Desktop applique aussi le fond d'écran LEOS A/B à l'écran de verrouillage natif de KDE via `kscreenlockerrc`, y compris son aperçu. Les deux valeurs précédentes sont sauvegardées avec le reste de l'identité visuelle et restaurées uniquement si elles n'ont pas été modifiées manuellement. LEOS ne remplace pas le dialogue natif d'authentification.
