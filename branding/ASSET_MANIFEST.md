# LEOS — Contrat des ressources visuelles

Ce document décrit les ressources officielles, leurs chemins de déploiement et leur état de vérification. Les fichiers présents dans le dépôt sont les références effectivement utilisées par la construction LEOS.

## Emblèmes

| Chemin | Usage |
| --- | --- |
| `branding/desktop-logo.jpeg` | Lion seul, Desktop Mode |
| `branding/gaming-logo.jpeg` | Lion avec manette, Gaming Mode |
| `branding/reference-comparison.jpeg` | Référence interne uniquement |

Le sélecteur QML charge les deux emblèmes avec chargement asynchrone. Les libellés textuels restent visibles si une image est absente ou illisible.

## Fond d'écran Desktop

| Chemin | Usage |
| --- | --- |
| `branding/wallpapers/desktop-leos.svg` | Fond LEOS Desktop 4K (3840 × 2160), lion seul, halos cyan/magenta discrets |
| `branding/wallpapers/gaming-leos.svg` | Fond LEOS Gaming 4K (3840 × 2160), lion avec manette, halos cyan/magenta plus dynamiques |

Chaque SVG référence le JPEG officiel correspondant par un lien relatif (`../desktop-logo.jpeg` ou `../gaming-logo.jpeg`) : l'emblème fourni reste la source unique, sans duplication ni déformation. La recette copie l'ensemble de `branding/` vers `/usr/share/leos/branding/`, ce qui conserve ces chemins relatifs. Les fonds sont fournis comme ressources ; ils ne sont pas appliqués automatiquement ni injectés dans le profil Plasma. Le rendu SVG avec image liée doit encore être validé dans une session Bazzite réelle.

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

Le fichier `branding/DEPLOYED_SHA256SUMS` contient les SHA-256 des huit ressources effectivement présentes dans le dépôt. Les trois JPEG ont été comparés aux originaux reçus : leurs empreintes correspondent exactement. Les trois vidéos hébergées ont des empreintes différentes de celles des vidéos originales fournies dans la conversation ; elles sont donc identifiées comme versions déployées distinctes, sans prétendre qu'elles sont binaires-identiques aux sources. Les deux SVG sont également suivis dans ce manifeste. Les workflows de validation et de publication vérifient désormais ces empreintes avant de poursuivre.

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

**Vérification CI :** `ffprobe` confirme pour chacune des trois vidéos la présence d'un flux vidéo et d'un flux audio, et relève les durées indiquées ci-dessus. `ffmpeg` décode ensuite chaque fichier jusqu'au bout sans erreur. Ces contrôles ne remplacent pas un test de lecture dans Qt Multimedia sur Bazzite. Les tailles des vidéos ne correspondent pas à celles des originaux précédemment reçus dans la conversation : leur identité binaire avec les originaux n'est donc pas confirmée. Ne pas présenter les empreintes SHA-256 des originaux comme celles des copies GitHub. La qualité visuelle, la synchronisation audio/vidéo et la lecture effective restent à valider sur une session Bazzite réelle.

## Identité visuelle

- Desktop utilise le lion seul.
- Gaming utilise le lion avec la manette.
- La référence comparative n'est jamais affichée comme logo de mode.
- Préserver les fichiers présents ; toute optimisation future doit produire une copie dérivée, sans écraser la source.
