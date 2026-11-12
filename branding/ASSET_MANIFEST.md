# LEOS — Contrat des ressources visuelles

Ce document définit les noms et conditions d'intégration des ressources officielles. Il ne crée aucun logo de remplacement : les fichiers graphiques doivent rester les références originales fournies par Jovan.

## Emblèmes

| Chemin attendu | Usage |
| --- | --- |
| `branding/desktop-logo.jpeg` | Lion seul, Desktop Mode |
| `branding/gaming-logo.jpeg` | Lion avec manette, Gaming Mode |
| `branding/reference-comparison.jpeg` | Référence interne uniquement ; jamais affichée comme logo principal |

Les deux emblèmes de mode doivent conserver le lion métallique, les accents cyan et magenta, la typographie et le fond de la référence. Ne pas recadrer les détails distinctifs ni redessiner le lion.

Les interfaces QML chargent les deux fichiers de mode depuis `branding/`. En leur absence, elles doivent conserver un repli typographique LEOS propre, sans substituer un visuel générique.

## Animations officielles

| Chemin attendu | Déclenchement |
| --- | --- |
| `branding/animations/desktop-intro.mp4` | Entrée dans Desktop Mode |
| `branding/animations/gaming-intro.mp4` | Chaque entrée dans Gaming Mode |

Les vidéos fournies par Jovan sont les références maîtresses. Leur mouvement, leur durée, leur composition et leur identité sonore ne doivent pas être réinterprétés sans demande. Préserver les fichiers originaux ; toute conversion éventuelle doit être une copie optimisée, jamais un remplacement destructif.

Avant d'activer la lecture dans l'interface, vérifier la disponibilité de Qt Multimedia dans l'image Bazzite ciblée et prévoir un comportement de repli si le décodage ou le fichier échoue. Les animations doivent respecter le réglage global LEOS permettant de les désactiver.

## Signatures sonores

| Chemin attendu | Déclenchement |
| --- | --- |
| `branding/sounds/desktop-intro.ogg` | Signature Desktop |
| `branding/sounds/gaming-intro.ogg` | Signature Gaming |

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

## État réel

La structure et les chemins attendus sont documentés. Les fichiers binaires officiels (logos séparés, vidéos et sons) ne sont pas encore présents dans le dépôt GitHub à la date de cette mise à jour. Ne pas déclarer leur intégration terminée avant de vérifier leur présence dans le dépôt et leur chargement dans une session Bazzite réelle.
