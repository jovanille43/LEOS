# Packaging système LEOS

Le code source reste organisé dans le dépôt ; BlueBuild le copie dans l'image pendant la construction.

## Emplacements prévus

- `/usr/share/leos/gaming` : application et backend Gaming.
- `/usr/share/leos/launcher` : sélecteur de mode et démarrage de session.
- `/usr/share/leos/control_center` : Centre de contrôle LEOS.
- `/usr/share/leos/controller_center` : détection, test et préférences locales des manettes.
- `/usr/share/leos/shop` : catalogue et interface de la boutique LEOS.
- `/usr/share/leos/leos_core` : préférences partagées.
- `/usr/share/leos/branding` : ressources visuelles officielles.
- `/usr/share/applications/leos-mode-selector.desktop` : entrée du sélecteur.
- `/usr/share/applications/leos-control-center.desktop` : entrée du Centre de contrôle.
- `/usr/share/applications/leos-controller-center.desktop` : entrée du Centre des manettes.
- `/usr/share/applications/leos-store.desktop` : entrée de la boutique LEOS.
- `/usr/etc/xdg/autostart/leos-session.desktop` : restauration du dernier mode après connexion.

## Dépendances système prévues

Le prototype utilise les paquets Fedora `python3-pyside6`, `python3-psutil` et `python3-evdev`. Ils seront intégrés via le module DNF de BlueBuild. Le paquet `python3-evdev` fournit les bindings Linux permettant d'identifier les périphériques d'entrée et de lire leurs événements depuis `/dev/input`. La lecture des entrées est utilisée sans envoyer d'événements ni modifier les mappings système.

La base KDE fournit déjà le framework Qt et les composants QML habituels, mais les modules QML réellement nécessaires seront confirmés pendant les tests de l'image.

## Préférences des manettes

Le Centre des manettes enregistre les profils, zones mortes et centres d'axes dans `~/.config/leos/controllers.json`, avec des permissions utilisateur restrictives. Il ne modifie ni les permissions udev, ni les règles système, ni les réglages Steam/Lutris. L'accès à un périphérique dépend donc des permissions de session Linux existantes.

Les noms de profils sont pour l'instant des préférences LEOS locales ; leur application aux jeux et aux lanceurs sera développée via les intégrations correspondantes, sans remappage global caché.

## Prudence

La recette de référence se trouve dans `recipes/recipe.yml`. L'action officielle BlueBuild recherche le fichier dans `recipes/` ou `config/`. La recette référence les paquets Fedora et copie les sources du dépôt dans l'image. Elle doit néanmoins être validée avec la version exacte du CLI BlueBuild et de Bazzite avant la première compilation. Les entrées menu/autostart ne seront actives qu'après installation effective du code par le workflow.


## Bibliothèque multi-lanceurs

Le backend Gaming détecte Steam, puis importe les manifestes locaux de Heroic/Legendary pour Epic, GOG et Amazon Games (installation native ou Flatpak). Les jeux sont ouverts via le protocole Heroic afin de conserver ses paramètres Wine/Proton par titre. LEOS ne lit ni ne modifie les jetons de connexion ou les données d'authentification. Lutris est également importé depuis sa base locale `pga.db`, ouverte avec SQLite en mode lecture seule (`mode=ro` et `query_only`). Les jeux sont lancés via `lutris:rungameid/<id>`, ce qui laisse Lutris gérer ses runners et ses réglages.
