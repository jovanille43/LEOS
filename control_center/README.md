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
