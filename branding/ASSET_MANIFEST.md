# LEOS — Contrat des ressources visuelles

Ce document définit les noms et conditions d'intégration des ressources officielles. Il ne crée aucun logo de remplacement : les fichiers graphiques doivent rester les références originales fournies par Jovan.

## Emblèmes

| Chemin attendu | Usage |
| --- | --- |
| `branding/desktop-logo.jpeg` | Lion seul, Desktop Mode |
| `branding/gaming-logo.jpeg` | Lion avec manette, Gaming Mode |
| `branding/reference-comparison.jpeg` | Référence interne uniquement ; jamais affichée comme logo principal |

Les deux emblèmes de mode doivent conserver le lion métallique, les accents cyan et magenta, la typographie et le fond de la référence. Ne pas recadrer les détails distinctifs ni redessiner le lion.

Le sélecteur QML charge les deux emblèmes depuis `branding/` avec un chargement asynchrone. En leur absence, les libellés textuels restent visibles ; aucun visuel générique n'est substitué.

## Animations officielles

| Chemin attendu | Déclenchement |
| --- | --- |
| `branding/animations/desktop-intro.mp4` | Entrée dans Desktop Mode |
| `branding/animations/gaming-intro.mp4` | Chaque entrée dans Gaming Mode |
| `branding/animations/gaming-roar-reference.mp4` | Référence secondaire uniquement ; non utilisée comme animation principale |

Les vidéos fournies par Jovan sont les références maîtresses. Leur mouvement, leur durée, leur composition et leur identité sonore ne doivent pas être réinterprétés sans demande. Préserver les fichiers originaux ; toute conversion éventuelle doit être une copie optimisée, jamais un remplacement destructif.

Le sélecteur et Gaming sont maintenant raccordés à Qt Multimedia : chaque choix de mode joue la vidéo correspondante, et le retour depuis Gaming joue l'introduction Desktop. Les pistes AAC restent synchronisées et peuvent être coupées séparément via `sounds_enabled`. Le lecteur possède un repli en cas d'erreur et un délai de sécurité de 9 secondes. Le paquet `qt6-qtmultimedia` est inclus dans la recette. Le fonctionnement réel des codecs et du module QML doit encore être validé dans une session Bazzite.

## Signatures sonores

| Chemin attendu | Déclenchement |
| --- | --- |
| Piste AAC de `branding/animations/desktop-intro.mp4` | Signature Desktop synchronisée |
| Piste AAC de `branding/animations/gaming-intro.mp4` | Signature Gaming synchronisée |

Les pistes audio AAC sont intégrées aux vidéos MP4 sources. Leur lecture doit rester synchronisée avec l'image et être désactivable indépendamment du reste des sons LEOS. Aucun fichier OGG séparé n'a été fourni.

## Ressources complémentaires

- `branding/wallpapers/desktop.png` — fond Desktop officiel.
- `branding/wallpapers/gaming.png` — fond Gaming officiel.
- `branding/icons/` — icônes et éléments graphiques LEOS.

## Packaging

La recette BlueBuild copie le dossier `branding/` dans l'arborescence LEOS sous `/usr/share/leos/`. Les chemins relatifs des interfaces doivent donc continuer à résoudre les ressources depuis cette arborescence.

## Références reçues et identification

Les fichiers sources ont été transmis dans la conversation le 12 novembre 2026 et leur contenu a été inspecté.

| Source reçue | Rôle canonique | Empreinte SHA-256 du fichier source |
| --- | --- | --- |
| `IMG_2598(2).jpeg` | `desktop-logo.jpeg` — lion seul, emblème Desktop | `7f36eca76b54641741384d614e39739a00c549eaf10ea7dceb752b66d9528548` |
| `IMG_2599(2).jpeg` | `gaming-logo.jpeg` — lion avec manette, emblème Gaming | `512f0b07cd6d028b25640eba50807b4d1e54d296c2197cfa5f6b2ebc523a8cbb` |
| `IMG_2591(1).jpeg` | `reference-comparison.jpeg` — planche comparative, référence uniquement | `eda3513c029385ca60c70d92fa8780adf97c31c4985e00bd1465d543ac0eb8f9` |
| `6af360efcc8e48ee89610680(1).mp4` | `animations/desktop-intro.mp4` — apparition progressive du lion seul puis du mot-symbole LEOS | `3b1b5d3775cbbb58a96542df2aafafc943f9782009d07ae2258399c956816bc0` |
| `video-6af35d8d3134ec85f320926c(2).mp4` | `animations/gaming-intro.mp4` — rugissement, éclat énergétique, apparition de la manette et emblème Gaming final | `1a622ea8f87faac42cf5e2a782f67425a8482789f0cb289d4b6a48d0a417dfcd` |
| `video-6af36284cc8e48ee89610c5c(1).mp4` | `animations/gaming-roar-reference.mp4` — variante de rugissement et transition vers le lion avec manette | `db26fa64ed7658f1f86322bc60e5b08201a6497c1740f439c6df1dc6138af4c9` |

Les trois animations sont des références distinctes. L'animation Gaming principale est celle qui se termine sur le lion tenant la manette, avec l'éclat cyan/magenta. La variante de rugissement est conservée comme référence secondaire et ne remplace pas l'animation principale.

**État de transfert :** contenu et rôles vérifiés, empreintes sources consignées. Les binaires canoniques ci-dessus ne sont pas encore présents dans l'arbre GitHub ; ne pas les déclarer intégrés ni les charger depuis des chemins inexistants. Les vidéos sources contiennent une piste audio AAC. Conserver les MP4 originaux comme références maîtresses afin de préserver le son et la synchronisation ; toute version optimisée doit être une copie dérivée avec audio, jamais un remplacement destructif.

## Vérification des fichiers sources — 12 novembre 2026

Les six originaux sont bien disponibles dans les pièces jointes de travail et ont été contrôlés directement :

| Fichier reçu | Taille | Dimensions / flux | SHA-256 |
| --- | ---: | --- | --- |
| `IMG_2598(2).jpeg` — Desktop | 67 277 octets | 1376 × 768 | `7f36eca76b54641741384d614e39739a00c549eaf10ea7dceb752b66d9528548` |
| `IMG_2599(2).jpeg` — Gaming | 73 084 octets | 1376 × 768 | `512f0b07cd6d028b25640eba50807b4d1e54d296c2197cfa5f6b2ebc523a8cbb` |
| `IMG_2591(1).jpeg` — comparaison | 105 202 octets | 1379 × 752 | `eda3513c029385ca60c70d92fa8780adf97c31c4985e00bd1465d543ac0eb8f9` |
| `6af360efcc8e48ee89610680(1).mp4` — Desktop | 1 183 500 octets | H.264, 682 × 510, AAC | `3b1b5d3775cbbb58a96542df2aafafc943f9782009d07ae2258399c956816bc0` |
| `video-6af35d8d3134ec85f320926c(2).mp4` — Gaming principal | 2 869 853 octets | H.264, 686 × 512, AAC | `1a622ea8f87faac42cf5e2a782f67425a8482789f0cb289d4b6a48d0a417dfcd` |
| `video-6af36284cc8e48ee89610c5c(1).mp4` — Gaming secondaire | 1 858 818 octets | H.264, 682 × 510, AAC | `db26fa64ed7658f1f86322bc60e5b08201a6497c1740f439c6df1dc6138af4c9` |

Les fichiers sont bien reçus et vérifiés. Le transfert des binaires dans GitHub reste une opération distincte : les outils de modification de fichiers texte ne permettent pas de pousser directement ces pièces jointes binaires. Ne pas confondre la vérification des originaux avec leur présence dans le dépôt.

## État réel

La structure et les chemins attendus sont documentés. Les fichiers binaires officiels (logos séparés, vidéos et sons) ne sont pas encore présents dans le dépôt GitHub à la date de cette mise à jour. Ne pas déclarer leur intégration terminée avant de vérifier leur présence dans le dépôt et leur chargement dans une session Bazzite réelle.
