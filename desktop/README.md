# LEOS — Desktop Mode

Desktop Mode conserve **KDE Plasma** comme bureau principal. LEOS ajoute progressivement une identité cohérente sans remplacer les mécanismes natifs de KDE/Bazzite.

## Éléments déjà préparés

- `applications/leos-mode-selector.desktop` : entrée de menu pour ouvrir le sélecteur Desktop/Gaming.
- `autostart/leos-session.desktop` : point d'entrée de session qui restaure Gaming si ce mode était le dernier utilisé. En mode Desktop, il se ferme sans action.
- `config/desktop-defaults.json` : profil déclaratif LEOS Original (palette sombre cyan/magenta, dock inférieur, applications épinglées indicatives et widgets facultatifs).

## Direction visuelle Desktop

- Emblème officiel du lion seul, dès que le fichier source sera ajouté au dépôt.
- Fond sombre LEOS, accents cyan et magenta, surfaces sobres et contrastes lisibles.
- Dock inférieur centré, personnalisable et désactivable.
- Widgets facultatifs, désactivés par défaut.
- Menu LEOS donnant accès aux applications, à la recherche, aux modes et au Centre de contrôle.

## Règles de personnalisation

Le profil JSON est une référence de conception, pas une configuration Plasma directement applicable. Il ne doit pas être présenté comme un thème déjà installé ou actif. L'application future devra sauvegarder les réglages KDE existants, vérifier les applications disponibles et demander le consentement avant toute modification du profil personnel.

Aucune configuration Plasma existante ne sera écrasée silencieusement.

## À finaliser

- Intégration de l'emblème et du fond d'écran officiels.
- Moteur de thème et configurateur du dock, avec sauvegarde/restauration.
- Menu principal LEOS et recherche universelle.
- Raccourcis globaux KDE personnalisables (dont Super+G / Super+D).
- Tests de session sur une vraie installation Bazzite KDE.

Le packaging installe les ressources de référence sous `/usr/share/leos/`. Les personnalisations Plasma avancées seront appliquées au profil utilisateur uniquement après validation explicite.


## Moteur de thèmes LEOS

Le paquet `desktop/themes.py` fournit les palettes LEOS Original, Light, Cyan,
Magenta et Gaming. Le Centre de contrôle les expose à ses composants QML et
actualise son apparence dès le changement de thème. Les préférences sont
conservées par `leos_core.SettingsStore`.

Cette première intégration concerne les interfaces LEOS. Elle ne modifie pas
les couleurs, le thème Plasma ou les fichiers de configuration KDE déjà présents
dans le profil utilisateur. L'application des thèmes à l'ensemble du bureau
Plasma et la gestion du dock restent des étapes distinctes, qui devront être
réversibles et activées explicitement.


## Profils de disposition et dock

Le module `desktop/layouts.py` enregistre les préférences de disposition dans
`~/.config/leos/desktop-layout.json` (ou sous `XDG_CONFIG_HOME`). Il propose
les profils LEOS par défaut, Minimal et Espace de travail, ainsi que des réglages
personnalisés pour la visibilité, la position, l'alignement et le masquage
automatique du dock. Les widgets sont désactivés par défaut.

Les données sont validées, écrites atomiquement et protégées par des permissions
utilisateur privées. Un fichier invalide est ignoré sans être écrasé. Le Centre
de contrôle expose ces préférences et les conserve entre les sessions.

**Limite actuelle :** ces réglages décrivent la disposition souhaitée, mais ne
reconfigurent pas encore le panneau Plasma. L'intégration Plasma devra détecter
la configuration active, créer une sauvegarde restaurable, vérifier les
applications épinglées et demander une confirmation explicite avant toute
modification. Le Centre de contrôle expose la création d'une sauvegarde. La restauration
reste une opération de maintenance explicite : elle n'est pas déclenchée depuis
l'interface tant que le comportement de Plasma pendant une session active n'a
pas été validé. Aucune commande de configuration KDE n'est exécutée par ce module.


## Sauvegarde et restauration Plasma

Le module `desktop/plasma_backup.py` sait sauvegarder le fichier de disposition
des panneaux Plasma de l'utilisateur, vérifier l'intégrité SHA-256 des copies
et restaurer une sauvegarde. Les copies et manifestes sont privés (répertoire
0700, fichiers 0600). Les sauvegardes sont stockées sous
`~/.local/state/leos/plasma-backups` ou sous `XDG_STATE_HOME`.

La restauration exige un indicateur de confirmation explicite fourni par
l'interface appelante. Avant de restaurer, le module sauvegarde également la
configuration courante afin de permettre un retour arrière. Aucun changement
n'est appliqué automatiquement à Plasma ; cette brique prépare la future
intégration du dock et des dispositions LEOS.


## Inspection Plasma et aperçu de disposition

Le module `desktop/plasma_inspector.py` analyse le fichier de configuration
Plasma en lecture seule. Il relève les conteneurs, panneaux et applets identifiés,
puis compare ces éléments aux préférences de disposition LEOS enregistrées.
L'interface affiche un rapport synthétique et une empreinte SHA-256 du fichier
inspecté.

Cette étape n'exécute aucune commande KDE et n'écrit aucun fichier. L'aperçu
indique les points à traiter, mais ne prétend pas produire un patch Plasma
applicable. Le moteur d'application reste désactivé (`can_apply=false`) tant
qu'il n'a pas été validé sur une véritable session Bazzite KDE. Une sauvegarde
préalable et une confirmation explicite resteront obligatoires.


## Adaptateur de panneaux LEOS (préparé, non activé)

Le module `desktop/plasma_adapter.py` génère un script utilisant l'API officielle
de scripting Plasma 6 pour créer, mettre à jour ou retirer un panneau LEOS.
Chaque panneau créé reçoit un marqueur privé `LEOS/managedBy=leos-panel-v1`.
Les opérations suivantes ne ciblent que ce marqueur : un panneau KDE personnel
ne peut pas être adopté ou supprimé implicitement.

L'adaptateur refuse de créer un second dock lorsqu'un panneau non géré existe
déjà, et refuse les versions antérieures à Plasma 6. Il préserve les widgets
déjà présents sur un panneau LEOS et n'ajoute que les widgets KDE disponibles.
Une tentative de mise à jour comporte un retour arrière en cas d'erreur.

**Cet adaptateur n'est pas encore exécuté par le Centre de contrôle.** Il n'a
pas été validé sur une vraie session Bazzite KDE ; aucune action d'application
n'est donc proposée dans l'interface. Les widgets de bureau restent hors du
périmètre de cette première version.

Références techniques : [API de scripting Plasma](https://develop.kde.org/docs/plasma/scripting/api/)
et [exécution des scripts Plasma](https://develop.kde.org/docs/plasma/scripting/).
