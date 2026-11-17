# LEOS — Contrat des ressources visuelles

Ce document décrit les ressources officielles, leurs chemins de déploiement et leur état de vérification. Les fichiers présents dans le dépôt sont les références effectivement utilisées par la construction LEOS.

## Emblèmes

| Chemin | Usage |
| --- | --- |
| `branding/desktop-logo.jpeg` | Lion seul, Desktop Mode |
| `branding/gaming-logo.jpeg` | Lion avec manette, Gaming Mode |
| `branding/desktop-logo-alpha.png` | Copie dérivée de `desktop-logo.jpeg` (fond noir rendu transparent), utilisée par le fond Desktop |
| `branding/gaming-logo-alpha.png` | Copie dérivée de `gaming-logo.jpeg` (fond noir rendu transparent), utilisée par le fond Gaming |
| `branding/reference-comparison.jpeg` | Référence interne uniquement |

Le sélecteur QML charge les deux emblèmes avec chargement asynchrone. Les libellés textuels restent visibles si une image est absente ou illisible.

## Fonds d'écran Desktop et Gaming

| Chemin | Usage |
| --- | --- |
| `branding/wallpapers/desktop-leos.svg` | Modèle officiel Desktop 4K (3840 × 2160), lion seul, halos A/B cyan/magenta d'origine |
| `branding/wallpapers/gaming-leos.svg` | Modèle officiel Gaming 4K (3840 × 2160), lion avec manette, halos plus dynamiques |

Ces deux SVG sont les sources maîtresses immuables et conservent les dégradés, courbes, proportions et positions d'emblèmes validés. Dans le Centre de contrôle, le bouton **Générer les fonds A/B** crée des copies personnalisées à partir de la paire active. Le générateur `desktop/wallpapers.py` ne remplace que les couleurs de halo/néon répertoriées ; les tons neutres, les géométries SVG et les images officielles des lions sont conservés.

Les variantes sont créées dans `$XDG_DATA_HOME/leos/wallpapers/A-<couleur-A>__B-<couleur-B>/` (par défaut sous `~/.local/share/leos/wallpapers/`). Chaque dossier contient les deux SVG et les deux PNG transparents correspondants, avec des liens d'image relatifs locaux. Une nouvelle paire reçoit un dossier distinct : générer un autre thème ne remplace donc pas les fichiers que KDE pourrait déjà afficher.

Les aperçus du Centre de contrôle se mettent à jour après génération. Le choix du fond reste manuel : le bouton de sélection ouvre le module KDE natif, où l'utilisateur parcourt le dossier généré et choisit Desktop ou Gaming. Aucun fond n'est appliqué automatiquement au changement de thème, à la connexion ou au changement de mode. Les SVG originaux, JPEG fournis et PNG transparents packagés ne sont jamais modifiés. Le rendu réel doit encore être validé dans une session Bazzite.

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
