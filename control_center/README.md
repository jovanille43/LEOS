# LEOS Control Center

Premier panneau de préférences LEOS réalisé avec Qt 6 / QML et PySide6.

## Préférences actuellement persistées

- Thème sélectionné (LEOS Original, Light, Cyan, Magenta, Gaming).
- Animations et sons LEOS activés/désactivés.
- Overlay Gaming activé/désactivé.
- Profil de performances sélectionné.

Les valeurs sont conservées dans `~/.config/leos/settings.json` (ou `$XDG_CONFIG_HOME/leos/settings.json`) et protégées par des permissions utilisateur.

## Limites

Le panneau enregistre les préférences, mais tous les moteurs d'application visuelle/sonore et de gestion des performances ne sont pas encore intégrés. La sélection d'un profil ne change pas encore les fréquences CPU/GPU. Les paramètres système avancés restent ouverts dans KDE System Settings.

Le prototype n'a pas encore été exécuté dans une session Bazzite/KDE.


## Vérification des mises à jour système

Le Centre de contrôle peut lancer `uupd update-check` via `pkexec` (uniquement pour vérifier si une mise à jour d'image existe). Les codes retour de uupd sont interprétés sans déclencher l'installation : 0 signifie qu'une mise à jour est disponible, 77 que l'image est à jour. Quand `bazzite-updater` est présent sur l'image, le bouton dédié ouvre son interface pour que l'utilisateur consulte les détails et choisisse l'installation.

Aucune commande d'installation, de déploiement ou de redémarrage n'est appelée par cette page. Le timer automatique livré par Bazzite et la politique rpm-ostree de l'image de base ne sont pas modifiés à ce stade. Cette intégration ne prétend donc pas encore désactiver les installations automatiques héritées de Bazzite.
