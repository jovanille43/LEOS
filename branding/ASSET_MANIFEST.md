# LEOS — Contrat des ressources visuelles

Ce document définit les noms et conditions d'intégration des ressources officielles. Il ne crée aucun logo de remplacement : les fichiers graphiques doivent rester les références originales fournies par Jovan.

## Emblèmes

| Chemin attendu | Usage |
| --- | --- |
| `branding/desktop-logo.png` | Lion seul, Desktop Mode |
| `branding/gaming-logo.png` | Lion avec manette, Gaming Mode |
| `branding/reference-comparison.png` | Référence interne uniquement ; jamais affichée comme logo principal |

Les deux emblèmes de mode doivent conserver le lion métallique, les accents cyan et magenta, la typographie et le fond de la référence. Ne pas recadrer les détails distinctifs ni redessiner le lion.

Les interfaces QML chargent les deux fichiers de mode depuis `branding/`. En leur absence, elles doivent conserver un repli typographique LEOS propre, sans substituer un visuel générique.

## Animations officielles

| Chemin attendu | Déclenchement |
| --- | --- |
| `branding/animations/desktop-intro.webm` | Entrée dans Desktop Mode |
| `branding/animations/gaming-intro.webm` | Chaque entrée dans Gaming Mode |

Les vidéos fournies par Jovan sont les références maîtresses. Leur mouvement, leur durée, leur composition et leur identité sonore ne doivent pas être réinterprétés sans demande. Préserver les fichiers originaux ; toute conversion éventuelle doit être une copie optimisée, jamais un remplacement destructif.

Avant d'activer la lecture dans l'interface, vérifier la disponibilité de Qt Multimedia dans l'image Bazzite ciblée et prévoir un comportement de repli si le décodage ou le fichier échoue. Les animations doivent respecter le réglage global LEOS permettant de les désactiver.

## Signatures sonores

| Chemin attendu | Déclenchement |
| --- | --- |
| `branding/sounds/desktop-intro.ogg` | Signature Desktop |
| `branding/sounds/gaming-intro.ogg` | Signature Gaming |

Les signatures sonores restent synchronisées avec leur animation. Elles doivent être désactivables indépendamment du reste des sons LEOS et ne doivent jamais être jouées si les sons sont désactivés.

## Ressources complémentaires

- `branding/wallpapers/desktop.png` — fond Desktop officiel.
- `branding/wallpapers/gaming.png` — fond Gaming officiel.
- `branding/icons/` — icônes et éléments graphiques LEOS.

## Packaging

La recette BlueBuild copie le dossier `branding/` dans l'arborescence LEOS sous `/usr/share/leos/`. Les chemins relatifs des interfaces doivent donc continuer à résoudre les ressources depuis cette arborescence.

## État réel

La structure et les chemins attendus sont documentés. Les fichiers binaires officiels (logos séparés, vidéos et sons) ne sont pas encore présents dans le dépôt GitHub à la date de cette mise à jour. Ne pas déclarer leur intégration terminée avant de vérifier leur présence dans le dépôt et leur chargement dans une session Bazzite réelle.
