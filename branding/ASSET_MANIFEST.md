# LEOS — Contrat des ressources visuelles

Ce document décrit les ressources officielles, leurs chemins de déploiement et leur état de vérification. Les fichiers présents dans le dépôt sont les références effectivement utilisées par la construction LEOS.

## Emblèmes

| Chemin | Usage |
| --- | --- |
| `branding/desktop-logo.png` | Lion seul, transparent et cadré pour les interfaces Desktop |
| `branding/gaming-logo.png` | Lion avec manette, transparent et cadré pour les interfaces Gaming |
| `branding/desktop-wallpaper-logo.png` | Lion seul sur canevas transparent 1376 × 768 pour le fond Desktop |
| `branding/gaming-wallpaper-logo.png` | Lion avec manette sur canevas transparent 1376 × 768 pour le fond Gaming |
| `branding/desktop-logo.jpeg`, `branding/gaming-logo.jpeg` | Sources officielles préservées et non affichées directement |
| `branding/reference-comparison.jpeg` | Référence interne uniquement |

Le sélecteur QML charge les deux PNG transparents avec chargement asynchrone. Les libellés textuels restent visibles si une image est absente ou illisible.

## Fond d'écran Desktop

| Chemin | Usage |
| --- | --- |
| `branding/wallpapers/desktop-leos.svg` | Fond source LEOS Desktop 4K (3840 × 2160), lion seul ; accents d'origine utilisés uniquement comme points de transformation A/B |
| `branding/wallpapers/gaming-leos.svg` | Fond source LEOS Gaming 4K (3840 × 2160), lion avec manette ; accents d'origine utilisés uniquement comme points de transformation A/B |

Chaque SVG référence la variante PNG transparente correspondante par un lien relatif (`../desktop-wallpaper-logo.png` ou `../gaming-wallpaper-logo.png`). Le canevas 16:9 conserve le cadrage du fond sans rectangle JPEG ; les PNG cadrés séparés servent aux interfaces. La recette copie explicitement les ressources nécessaires vers `/usr/share/leos/branding/`, ce qui conserve ces chemins relatifs, sans embarquer les fichiers sources et références. Au premier démarrage, LEOS génère des variantes privées recolorées à partir des couleurs A/B choisies ; seule la variante personnalisée Desktop est appliquée après confirmation et sauvegarde Plasma. Les accents des SVG d'origine sont des entrées techniques de recoloration, jamais une palette utilisateur imposée. Le rendu SVG avec image liée doit encore être validé dans une session KDE réelle.

## Animations intégrées

| Chemin | Déclenchement |
| --- | --- |
| `branding/animations/desktop-intro.mov` | Entrée dans Desktop Mode et retour depuis Gaming |
| `branding/animations/gaming-intro.mp4` | Chaque entrée dans Gaming Mode |
| `branding/animations/gaming-roar-reference.mp4` | Variante de référence, non jouée automatiquement |

Les noms reflètent les extensions des fichiers téléversés. La vidéo Desktop a été fournie sous le nom `Lion desktop.mov` : elle reste donc au format MOV au lieu d'être artificiellement renommée en MP4. Les deux vidéos Gaming proviennent de fichiers portant l'extension MP4.

Le sélecteur et Gaming utilisent Qt Multimedia. Les pistes audio des vidéos sont conservées et peuvent être coupées via le réglage `sounds_enabled`. Si la lecture échoue, le délai de sécurité permet de terminer la transition au lieu de bloquer l'interface. Le paquet `qt6-qtmultimedia` est inclus dans la recette BlueBuild.

## Packaging

La recette `recipes/common-modules.yml` copie uniquement les ressources nécessaires à l'exécution vers `/usr/share/leos/branding/`. Depuis les QML installés sous `/usr/share/leos/launcher/qml/` et `/usr/share/leos/gaming/qml/`, les chemins relatifs `../../branding/` résolvent vers ce dossier.

## Intégrité des fichiers déployés

Le fichier `branding/DEPLOYED_SHA256SUMS` suit uniquement les huit ressources graphiques et vidéos nécessaires à l'exécution. Les JPEG sources officiels restent dans le dépôt pour régénérer les PNG transparents ; `reference-comparison.jpeg` et `gaming-roar-reference.mp4` sont des références internes non embarquées. Les empreintes des fichiers déployés sont contrôlées avant la construction et la publication.

## État des fichiers présents sur GitHub

Les sources JPEG sont préservées et quatre PNG transparents sont déployés en plus. Les JPEG ne sont plus utilisés directement dans les interfaces. Les trois vidéos ont été déplacées dans `branding/animations/` et renommées sans réencodage effectué par cette opération Git.

| Ressource | Taille GitHub |
| --- | ---: |
| `desktop-logo.jpeg` | 67 277 octets |
| `gaming-logo.jpeg` | 73 084 octets |
| `desktop-logo.png` (597 × 685, alpha) | 409 516 octets |
| `gaming-logo.png` (677 × 686, alpha) | 462 238 octets |
| `desktop-wallpaper-logo.png` (1376 × 768, alpha) | 451 407 octets |
| `gaming-wallpaper-logo.png` (1376 × 768, alpha) | 497 896 octets |
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

## Identité système avant et après connexion

| Ressource | Rôle |
| --- | --- |
| branding/plymouth/leos/leos.plymouth | Plymouth sombre et métallique, sans accents A/B imposés |
| branding/sddm/leos/Main.qml | Écran de connexion SDDM Qt 6 |
| plasma-theme/look-and-feel/org.leos.desktop/contents/splash/Splash.qml | Écran de chargement après connexion |
| icons/leos/cursors_scalable/default/default.svg | Flèche standard LEOS, recolorée A/B |
| files/scripts/prepare-leos-cursors.sh | Génération à la construction des 11 formes SVG de curseur, avec points chauds par type |
| aurorae/leos/decoration.svg et les SVG de boutons | Modèles de cadres de fenêtres et boutons, recolorés A/B dans une variante utilisateur |

Le script files/scripts/prepare-leos-plymouth.sh convertit l'emblème Desktop officiel en watermark PNG pendant la construction. La recette installe le dossier source branding dans /usr/share/leos/branding/ (et non à la racine de /usr/share/leos), emplacement attendu par les lanceurs, les fonds d'écran, SDDM, Plasma et Plymouth. L'initramfs est régénéré par BlueBuild pour embarquer le thème Plymouth. SDDM utilise le thème Qt 6 fourni par LEOS. Les paramètres personnels de splash Plasma, de curseur, de décor Aurorae et de fond d'écran de verrouillage sont appliqués uniquement lorsque l'utilisateur accepte le profil Desktop ; leurs anciennes valeurs restent restaurables.
