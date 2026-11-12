# Packaging système LEOS

Le code source reste organisé dans le dépôt ; BlueBuild le copie dans l'image pendant la construction.

## Emplacements prévus

- `/usr/share/leos/gaming` : application et backend Gaming.
- `/usr/share/leos/launcher` : sélecteur de mode et démarrage de session.
- `/usr/share/leos/control_center` : Centre de contrôle LEOS et raccourcis allowlistés vers les modules KDE natifs.

Le fichier `control_center/settings_modules.py` contient l'association entre les clés de l'interface et les modules KCM KDE. La construction de commande est testée sans dépendre d'une session Plasma ; le lancement utilise `QProcess` avec une liste d'arguments explicite, jamais un shell. Les modules sont ouverts via `kcmshell6` lorsque disponible, sinon via `systemsettings`. La disponibilité exacte des modules KCM sera contrôlée sur la première image LEOS.

La vue d'ensemble du Centre de contrôle réutilise `gaming.backend.system_monitor.SystemMonitor` au lieu de lancer un deuxième collecteur. Elle affiche l'utilisation CPU et mémoire, la température CPU lorsque le capteur est exposé, l'occupation de la racine `/` et les débits réseau agrégés en réception/émission. Les vitesses réseau nécessitent deux échantillons avant d'être calculées. Le moniteur actualise ses données toutes les deux secondes et reste strictement en lecture seule. Les valeurs indisponibles ne sont pas estimées.
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

Le prototype utilise les paquets Fedora `python3-pyside6`, `python3-psutil`, `python3-evdev` et `qt6-qtmultimedia`. Ils sont intégrés via le module DNF de BlueBuild. Qt Multimedia fournit les types QML `MediaPlayer`, `VideoOutput` et `AudioOutput` pour les introductions de modes. Le paquet `python3-evdev` fournit les bindings Linux permettant d'identifier les périphériques d'entrée et de lire leurs événements depuis `/dev/input`.

Le backend ouvre les périphériques en lecture seule et utilise leur descripteur non bloquant pour que la surveillance périodique ne bloque pas l'interface Qt. Lorsque `InputDevice(readonly=True)` est disponible (python-evdev 2.0+), il utilise l'API publique. Pour la branche Fedora 1.9.x, qui ne propose pas encore cet argument, un adaptateur ouvre explicitement le fichier avec `O_RDONLY | O_NONBLOCK` et initialise les métadonnées nécessaires à partir des helpers ioctl de python-evdev. LEOS n'envoie aucun événement, ne saisit pas le périphérique avec `EVIOCGRAB` et ne modifie ni permissions udev ni mappings système.

La base KDE fournit déjà le framework Qt et les composants QML habituels. Le module Qt Multimedia est explicitement installé par la recette ; sa découverte QML, les codecs AAC/H.264 et la sortie audio/vidéo doivent encore être vérifiés sur l'image Bazzite réelle.

## Bluetooth

LEOS s'appuie sur les composants Bluetooth natifs de Bazzite KDE : BlueZ et son service système, l'intégration KDE Bluedevil/BluezQt et PipeWire pour l'audio Bluetooth. Aucun daemon ni gestionnaire parallèle n'est prévu. La recette ne force pas encore l'ajout de paquets BlueZ ni l'activation d'un service avant d'avoir inspecté l'image Bazzite de référence : cette vérification évite les doublons et doit confirmer le comportement réel de la base. Les contrôles de présence du service, de l'interface KDE, des profils audio et des périphériques sont listés dans [docs/bluetooth.md](bluetooth.md).

## Préférences des manettes

Le Centre des manettes enregistre les profils, zones mortes et centres d'axes dans `~/.config/leos/controllers.json`, avec des permissions utilisateur restrictives. Il ne modifie ni les permissions udev, ni les règles système, ni les réglages Steam/Lutris. L'accès à un périphérique dépend donc des permissions de session Linux existantes.

Le profil « Automatique » est sélectionné par défaut. LEOS s'appuie sur le nom du périphérique et les identifiants USB connus pour reconnaître certaines manettes Nintendo Switch, Sony PlayStation et Microsoft Xbox. En cas d'identification incertaine, la disposition Standard est conservée ; l'utilisateur peut toujours imposer un profil manuel. Les profils enregistrés sont chargés par le Gaming Mode pour sa propre navigation (notamment l'inversion confirmer/retour Nintendo, la zone morte et le centre des sticks). Ils ne remappent pas les commandes des jeux externes : Steam et les lanceurs conservent leur configuration, sans remappage global caché.

## Prudence

La recette de référence se trouve dans `recipes/recipe.yml`. L'action officielle BlueBuild recherche le fichier dans `recipes/` ou `config/`. La recette référence les paquets Fedora et copie les sources du dépôt dans l'image. Elle doit néanmoins être validée avec la version exacte du CLI BlueBuild et de Bazzite avant la première compilation. Les entrées menu/autostart ne seront actives qu'après installation effective du code par le workflow.


## Bibliothèque multi-lanceurs

Le backend Gaming détecte Steam, puis importe les manifestes locaux de Heroic/Legendary pour Epic, GOG et Amazon Games (installation native ou Flatpak). Les jeux sont ouverts via le protocole Heroic afin de conserver ses paramètres Wine/Proton par titre. LEOS ne lit ni ne modifie les jetons de connexion ou les données d'authentification. Lutris est également importé depuis sa base locale `pga.db`, ouverte avec SQLite en mode lecture seule (`mode=ro` et `query_only`). Les jeux sont lancés via `lutris:rungameid/<id>`, ce qui laisse Lutris gérer ses runners et ses réglages.


## Applications par défaut et désinstallation

Brave, LibreOffice et VLC sont proposées comme applications facultatives par le service `leos-default-apps.service`. **Aucune installation ni ajout de dépôt Flatpak n'a lieu sans une confirmation explicite** dans la boîte de dialogue KDE ; le choix par défaut est le refus. Si l'utilisateur refuse, le service mémorise ce choix et ne repose pas la question à chaque connexion. Si la confirmation graphique ou Flatpak est indisponible, aucune installation n'est lancée. Après accord, les applications déjà présentes dans une installation utilisateur ou système sont ignorées. Le marqueur `~/.local/state/leos/default-apps-seeded` évite de reproposer l'installation après réussite ou refus ; une erreur d'installation ne crée pas le marqueur et permet une nouvelle tentative.

La boutique gère les désinstallations Flatpak dans les deux portées :
- `--user` pour une application installée dans le profil utilisateur ;
- `--system` pour une application installée pour tout le système, avec authentification administrateur si nécessaire.

La suppression des données personnelles d'une application n'est jamais forcée par la boutique. Les paquets RPM/OSTree qui composent Bazzite ne sont pas supprimés par cette interface : ils relèvent des mécanismes système de Bazzite.
