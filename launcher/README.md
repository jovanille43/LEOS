# LEOS Mode Launcher

Ce dossier contient le sélecteur Desktop/Gaming et le point d'entrée de session.

- `main.py --select` ouvre le sélecteur de mode.
- `main.py` sans argument lit le dernier mode enregistré et ouvre Gaming si nécessaire ; en Desktop, KDE reste simplement affiché.
- `mode_manager.py` stocke le dernier mode utilisé via les préférences partagées de `leos_core`.

Le sélecteur permet déjà de mémoriser le mode choisi et de lancer l'application Gaming dans un environnement de développement où PySide6 est installé.

## Limites à ce stade

- Les raccourcis affichés dans le sélecteur sont des raccourcis de fenêtre, pas encore des raccourcis globaux KDE.
- Les applications du bureau restent en arrière-plan lors de l'ouverture de Gaming. Aucune fermeture automatique d'applications n'est implémentée.
- L'installation des entrées de menu et de l'autostart dans l'image Bazzite sera réalisée par le packaging BlueBuild.
- Les logos individuels officiels sont attendus dans `branding/desktop-logo.png` et `branding/gaming-logo.png`. En leur absence, les titres textuels servent de fallback.

Le sélecteur et l'autostart n'ont pas encore été testés dans une session KDE réelle.
