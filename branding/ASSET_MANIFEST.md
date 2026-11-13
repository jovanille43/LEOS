# LEOS — Contrat des ressources visuelles

Ce document décrit les ressources officielles, leurs chemins de déploiement et leur état de vérification. Les fichiers présents dans le dépôt sont les références effectivement utilisées par la construction LEOS.

## Emblèmes

| Chemin | Usage |
| --- | --- |
| `branding/desktop-logo.jpeg` | Lion seul, Desktop Mode |
| `branding/gaming-logo.jpeg` | Lion avec manette, Gaming Mode |
| `branding/desktop-logo-alpha.png` | Copie dérivée de `desktop-logo.jpeg` (fond noir rendu transparent), utilisée par le fond et l'interface Desktop |
| `branding/gaming-logo-alpha.png` | Copie dérivée de `gaming-logo.jpeg` (fond noir rendu transparent), utilisée par le fond et l'interface Gaming |
| `branding/reference-comparison.jpeg` | Référence interne uniquement |

Le sélecteur de modes, le menu Desktop et l'en-tête Gaming chargent les PNG transparents avec chargement asynchrone. Cela évite les rectangles noirs opaques des JPEG sur les panneaux colorés. Les libellés textuels restent visibles si une image est absente ou illisible.

## Fond d'écran Desktop

| Chemin | Usage |
| --- | --- |
| `branding/wallpapers/desktop-leos.svg` | Fond LEOS Desktop 4K (3840 × 2160), lion seul, halos cyan/magenta discrets |
| `branding/wallpapers/gaming-leos.svg` | Fond LEOS Gaming 4K (3840 × 2160), lion avec manette, halos cyan/magenta plus dynamiques |

Chaque SVG référence par un lien relatif (`../desktop-logo-alpha.png` ou `../gaming-logo-alpha.png`) une copie dérivée du JPEG officiel correspondant : le JPEG fourni reste la source unique et n'est jamais modifié, la copie est régénérable à l'identique avec `python3 tools/derive_emblem_alpha.py` (vérification : `--check`). Le PNG supprime le rectangle noir que le JPEG, sans transparence, dessinait sur les halos du fond ; composé sur du noir, il redonne l'emblème d'origine à 4 niveaux près. Les courbes décoratives du fond Gaming s'arrêtent avant le halo de l'emblème, qui n'est plus masqué par un rectangle noir. La recette copie l'ensemble de `branding/` vers `/usr/share/leos/branding/`, ce qui conserve ces chemins relatifs. Les fonds sont fournis comme ressources ; ils ne sont pas appliqués automatiquement ni injectés dans le profil Plasma. Le rendu SVG avec image liée doit encore être validé dans une session Bazzite réelle.

## Animations intégrées

| Chemin | Déclenchement |
| --- | --- |
| `branding/animations/desktop-intro.mov` | Entrée dans Desktop Mode et retour depuis Gaming |
| `branding/animations/gaming-intro.mp4` | Chaque entrée dans Gaming Mode |
| `branding/animations/gaming-roar-reference.mp4` | Variante de référence, non jouée automatiquement |

Les noms reflètent les extensions des fichiers téléversés. La vidéo Desktop a été fournie sous le nom `Lion desktop.mov` : elle reste donc au format MOV au lieu d'être artificiellement renommée en MP4. Les deux vidéos Gaming proviennent de fichiers portant l'extension MP4.

Le sélecteur et Gaming utilisent Qt Multimedia. Les pistes audio des vidéos sont conservées et peuvent être coupées via le réglage `sounds_enabled`. Si la lecture échoue, le délai de sécurité permet de terminer la transition au lieu de bloquer l'interface. Le paquet `qt6-qtmultimedia` est inclus dans la recette BlueBuild.

## Packaging

La recette `recipes/recipe.yml` copie l'intégralité de `branding/` vers `/usr/share/leos/branding/`. Depuis les QML installés sous `/usr/share/leos/launcher/qml/` et `/usr/share/leos/gaming/qml/`, les chemins relatifs `../../branding/` résolvent vers ce dossier.

## Intégrité des fichiers déployés

Le fichier `branding/DEPLOYED_SHA256SUMS` contient les SHA-256 des dix ressources effectivement présentes dans le dépôt. Les trois JPEG et les trois vidéos ont été comparés aux fichiers originaux fournis par le propriétaire du projet le 13 novembre 2026 : leurs SHA-256 sont strictement identiques (`IMG_2598.JPG` = `desktop-logo.jpeg`, `IMG_2599.JPG` = `gaming-logo.jpeg`, `IMG_2591.JPG` = `reference-comparison.jpeg`, `Lion_desktop.mov` = `animations/desktop-intro.mov`, `Lion_gaming.MP4` = `animations/gaming-intro.mp4`, `Lion_face_.MP4` = `animations/gaming-roar-reference.mp4`). Les deux SVG et les deux PNG dérivés sont également suivis dans ce manifeste. Les workflows de validation et de publication vérifient désormais ces empreintes avant de poursuivre.

## État des fichiers présents sur GitHub

Les trois images sont présentes sous leurs noms canoniques. Les trois vidéos ont été déplacées dans `branding/animations/` et renommées sans réencodage effectué par cette opération Git.

| Ressource | Taille GitHub |
| --- | ---: |
| `desktop-logo.jpeg` | 67 277 octets |
| `gaming-logo.jpeg` | 73 084 octets |
| `reference-comparison.jpeg` | 105 202 octets |
| `animations/desktop-intro.mov` | 2 934 309 octets |
| `animations/gaming-intro.mp4` | 2 115 657 octets |
| `animations/gaming-roar-reference.mp4` | 2 763 575 octets |

Métadonnées relevées par CI pour les vidéos :

| Vidéo | Codec vidéo / audio | Résolution | Durée |
| --- | --- | ---: | ---: |
| `desktop-intro.mov` | H.264 / AAC | 1112 × 834 | 5,354 s |
| `gaming-intro.mp4` | H.264 / AAC | 1112 × 828 | 6,048 s |
| `gaming-roar-reference.mp4` | H.264 / AAC | 1112 × 834 | 6,080 s |

Format : les vidéos sont d'origine en 4:3 (1112 × 834, et 1112 × 828 pour l'intro Gaming). Les lecteurs (`launcher/qml/ModeSelector.qml`, `gaming/qml/Main.qml`) les affichent en `PreserveAspectFit` sur un fond `#000000`, et le fond des vidéos est quasi noir (bords ≤ 9 sur 255 hors flashs néon) : les bandes sur un écran 16:9 ne sont pas visibles. Ne pas les réencoder ni les agrandir : ce serait une perte de qualité sans gain visible.

**Vérification CI :** `ffprobe` confirme pour chacune des trois vidéos la présence d'un flux vidéo et d'un flux audio, et relève les durées indiquées ci-dessus. `ffmpeg` décode ensuite chaque fichier jusqu'au bout sans erreur. Les comparaisons SHA-256 confirment que les trois vidéos du dépôt sont binaires-identiques aux originaux fournis. Ces contrôles ne remplacent pas un test de lecture dans Qt Multimedia sur Bazzite. La qualité visuelle, la synchronisation audio/vidéo et la lecture effective restent à valider sur une session Bazzite réelle.

## Identité visuelle

- Desktop utilise le lion seul.
- Gaming utilise le lion avec la manette.
- La référence comparative n'est jamais affichée comme logo de mode.
- Préserver les fichiers présents ; toute optimisation future doit produire une copie dérivée, sans écraser la source.
