# Packaging système LEOS

Le code source reste organisé dans le dépôt ; BlueBuild le copie dans l'image pendant la construction.

## Emplacements prévus

- `/usr/share/leos/gaming` : application et backend Gaming.
- `/usr/share/leos/launcher` : sélecteur de mode et démarrage de session.
- `/usr/share/leos/control_center` : Centre de contrôle LEOS.
- `/usr/share/leos/shop` : catalogue et interface de la boutique LEOS.
- `/usr/share/leos/leos_core` : préférences partagées.
- `/usr/share/leos/branding` : ressources visuelles officielles.
- `/usr/share/applications/leos-mode-selector.desktop` : entrée du sélecteur.
- `/usr/share/applications/leos-control-center.desktop` : entrée du Centre de contrôle.
- `/usr/share/applications/leos-store.desktop` : entrée de la boutique LEOS.
- `/usr/etc/xdg/autostart/leos-session.desktop` : restauration du dernier mode après connexion.

## Dépendances système prévues

Le prototype utilise les paquets Fedora `python3-pyside6` et `python3-psutil`. Ils seront intégrés via le module DNF de BlueBuild. La base KDE fournit déjà le framework Qt et les composants QML habituels, mais les modules QML réellement nécessaires seront confirmés pendant les tests de l'image.

## Prudence

La recette référence les paquets Fedora et copie les sources du dépôt dans l'image. Elle doit néanmoins être validée avec la version exacte du CLI BlueBuild et de Bazzite avant la première compilation. Les entrées menu/autostart ne seront actives qu'après installation effective du code par le workflow.
