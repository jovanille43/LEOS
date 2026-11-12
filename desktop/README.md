# LEOS — Desktop Mode

Desktop Mode conserve **KDE Plasma** comme bureau principal. LEOS ajoute progressivement une identité cohérente sans remplacer les mécanismes natifs de KDE/Bazzite.

## Éléments déjà préparés

- `applications/leos-mode-selector.desktop` : entrée de menu pour ouvrir le sélecteur Desktop/Gaming.
- `autostart/leos-session.desktop` : affiche le sélecteur de modes à chaque ouverture de session KDE. Le dernier mode utilisé y est rappelé ; le choix reste explicite.
- `config/desktop-defaults.json` : profil déclaratif LEOS Original (palette sombre cyan/magenta, dock inférieur, applications épinglées indicatives et widgets facultatifs).

## Direction visuelle Desktop

- Emblème officiel du lion seul, dès que le fichier source sera ajouté au dépôt.
- Fond sombre LEOS, accents cyan et magenta, surfaces sobres et contrastes lisibles.
- Dock inférieur centré, personnalisable et désactivable.
- Widgets facultatifs, désactivés par défaut.
- Menu LEOS donnant accès aux applications, à la recherche, aux catégories, aux favoris et aux applications récemment utilisées ; navigation clavier et effacement explicite de l’historique.
- Historique local borné à 20 identifiants `.desktop` ; aucune commande de lancement ni chemin privé n’est conservé.

## Règles de personnalisation

Le profil JSON est une référence de conception, pas une configuration Plasma directement applicable. Il ne doit pas être présenté comme un thème déjà installé ou actif. L'application future devra sauvegarder les réglages KDE existants, vérifier les applications disponibles et demander le consentement avant toute modification du profil personnel.

Aucune configuration Plasma existante ne sera écrasée silencieusement.

## À finaliser

- Intégration de l'emblème et du fond d'écran officiels.
- Application automatique des profils de disposition au véritable panneau Plasma (l'adaptateur de panneau existe mais reste inactif) ; dock et widgets encore non intégrés.
- Recherche universelle dans les réglages système et les applications, au-delà du catalogue du menu LEOS.
- Raccourcis globaux KDE personnalisables (dont Super+G / Super+D).
- Tests de session sur une vraie installation Bazzite KDE.

Le packaging installe les ressources de référence sous `/usr/share/leos/`. Les personnalisations Plasma avancées seront appliquées au profil utilisateur uniquement après validation explicite.


## Moteur de thèmes LEOS

Le paquet `desktop/themes.py` fournit les palettes LEOS Original, Light, Cyan,
Magenta et Gaming. Le Centre de contrôle les expose à ses composants QML et
actualise son apparence dès le changement de thème. Les préférences sont
conservées par `leos_core.SettingsStore`.

Par défaut, le choix de palette modifie uniquement les interfaces LEOS.
Une action distincte dans le Centre de contrôle permet, après confirmation,
d'exporter le thème sous forme de schéma KDE `.colors` dans l'espace utilisateur
`$XDG_DATA_HOME/color-schemes` (par défaut `~/.local/share/color-schemes`),
puis d'appeler `plasma-apply-colorscheme` sans shell.

L'application est limitée au schéma de couleurs KDE : elle ne remplace pas le
Plasma Style, les icônes, les curseurs, le fond d'écran, les panneaux, ni les
écrans de connexion. Seuls les composants KDE/Qt et éléments Plasma qui
respectent le schéma global changent. Le système immuable Bazzite n'est pas
modifié.

Avant application, LEOS mémorise le nom du schéma actif non-LEOS afin de
permettre sa restauration depuis le Centre de contrôle. Si le schéma actif ne
peut pas être identifié, si le fichier LEOS existe déjà sous une forme
différente, ou si l'état de restauration est absent alors qu'un thème LEOS est
déjà actif, l'application est refusée. Les fichiers .colors existants ne sont
jamais écrasés s'ils diffèrent du contenu généré par LEOS.


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
de scripting Plasma 6 pour créer un panneau LEOS ou actualiser un panneau déjà
marqué comme appartenant à LEOS. Chaque panneau créé reçoit un marqueur privé
`LEOS/managedBy=leos-panel-v1`.

L'adaptateur refuse de toucher à un panneau KDE personnel et refuse de créer
un second dock lorsqu'un panneau non géré existe déjà. Il refuse également les
versions antérieures à Plasma 6. Lors de la création, il vérifie la disponibilité
des widgets KDE ; lors d'une mise à jour, il ne cible que le panneau marqué LEOS.

**Limites de sécurité actuelles :** l'adaptateur n'est pas exécuté par le Centre
de contrôle et n'a pas été validé sur une vraie session Bazzite KDE. La
désactivation/suppression d'un panneau LEOS n'est pas encore implémentée ; les
panneaux existants restent intacts. Les widgets de bureau ne sont pas encore
appliqués. Toute future activation exigera une sauvegarde et une confirmation
explicite.

Références techniques : [API de scripting Plasma](https://develop.kde.org/docs/plasma/scripting/api/)
et [exécution des scripts Plasma](https://develop.kde.org/docs/plasma/scripting/).



## Schémas de couleurs KDE

Le module `desktop/kde_colors.py` convertit les cinq palettes LEOS en schémas
KDE au format INI standard. Les schémas sont créés dans l'espace de données de
l'utilisateur et identifiés comme gérés par LEOS. Une collision avec un fichier
différent n'est jamais écrasée.

Le Centre de contrôle présente l'action **Appliquer à KDE** et demande une
confirmation explicite. Il appelle ensuite l'outil natif
`plasma-apply-colorscheme` avec un argument fixe, sans shell. La commande
modifie la configuration de couleurs du profil utilisateur, pas l'image
système Bazzite. Le nom du schéma non-LEOS actif est enregistré avant
l'application ; une seconde confirmation permet de restaurer ce schéma.

Cette intégration ne constitue pas encore un Plasma Style complet. Les effets
sur les applications GTK dépendent de l'intégration KDE/GTK installée et les
applications déjà ouvertes peuvent nécessiter un redémarrage pour prendre en
compte les nouvelles couleurs.

Références : [documentation KDE sur les schémas de couleurs](https://docs.kde.org/stable_kf6/en/plasma-workspace/kcontrol/colors/)
et [format des couleurs Plasma](https://develop.kde.org/docs/plasma/theme/theme-details/).


## Plasma Style LEOS — première version

Le paquet source `plasma-theme/leos/` fournit un Plasma Style natif pour Plasma 6,
installé par BlueBuild dans `/usr/share/plasma/desktoptheme/leos/`. Il comprend
les métadonnées Plasma 6, un réglage discret du contraste/flou et trois fonds
SVG : panneau, fenêtre contextuelle et widget de bureau. Les autres éléments
utilisent le repli Breeze de Plasma afin de préserver la compatibilité.

Le Centre de contrôle vérifie la présence du paquet et de
`plasma-apply-desktoptheme`. L'application du style et sa restauration sont
protégées par une confirmation distincte. Le style précédent est enregistré
dans `$XDG_STATE_HOME/leos/plasma-style.json` avec des permissions privées.
La commande native de KDE est appelée sans shell ; aucun fichier système ou
`plasmarc` n'est modifié directement par LEOS.

**Limites alpha :** les trois SVG sont des premières formes originales et ne
constituent pas encore un habillage exhaustif. Les icônes, boutons et contrôles
Qt continuent d'utiliser leurs styles existants. L'emblème officiel du lion
n'est pas encore intégré, car les ressources graphiques originales ne sont
pas présentes dans le dépôt. Le style est installé mais n'est pas sélectionné
automatiquement. Son rendu doit encore être contrôlé sur une vraie session
Bazzite KDE, notamment les marges SVG, le flou et le comportement des panneaux.

Références KDE : [création d'un Plasma Style](https://develop.kde.org/docs/plasma/theme/quickstart/),
[structure et emplacements](https://develop.kde.org/docs/plasma/theme/theme-details/)
et [référence des éléments SVG](https://develop.kde.org/docs/plasma/theme/theme-elements/).


### Favoris du dock

Le module `desktop/dock_favourites.py` ajoute un stockage local des applications
épinglées dans `~/.config/leos/dock-favourites.json`. Il conserve uniquement
des identifiants de fichiers `.desktop`, jamais des commandes arbitraires ou
des chemins d'exécution. Les favoris peuvent être ajoutés, retirés et réordonnés.
La liste est bornée à 32 entrées, validée, écrite atomiquement et protégée en
permissions privées. Les identifiants ne sont pas encore résolus en icônes ni
appliqués au panneau Plasma : cette étape attend l'intégration visuelle et les
tests sur une session Bazzite KDE.


## Menu principal LEOS — première alpha

`menu_main.py`, `menu_controller.py` et `qml/Menu.qml` fournissent une
première interface de recherche et de lancement d'applications. Le catalogue
lit les fichiers `.desktop` système et utilisateur, filtre sans distinction de casse
ou d'accents par nom, identifiant, description et catégorie, et lance le programme
sans shell via `QProcess.startDetached`.
Les commandes non résolues et les entrées invalides sont refusées. Les codes `Exec` sont développés selon la spécification freedesktop ; `TryExec` est vérifié et les entrées `Terminal=true` sont masquées tant qu'aucun terminal n'est intégré. Le menu est
accessible depuis l'entrée **LEOS — Applications** et utilise son icône dédiée
cyan/bleu/violet/magenta.

Cette version est un lanceur de fenêtre autonome, pas encore un remplacement
du menu Plasma ni un dock intégré. La catégorie Favoris affiche les applications épinglées dans leur ordre personnalisé et conserve la recherche accent-insensible. La catégorie « Récemment utilisées » repose sur les lancements enregistrés localement. Les favoris ne sont pas encore appliqués au panneau Plasma ; les raccourcis globaux KDE restent à raccorder. Le rendu et le lancement doivent encore être validés sur une session Bazzite KDE réelle.

### Menu LEOS — favoris connectés au dock

Le catalogue du menu utilise désormais le stockage `DockFavourites` : chaque carte d'application propose une étoile pour épingler ou retirer l'application des favoris. Le choix est conservé dans le fichier local privé du dock ; le menu ne modifie toujours pas la configuration Plasma. Les commandes de lancement restent séparées des identifiants favoris et sont exécutées sans shell. Le raccourci `leos-menu.desktop` est inclus dans la recette BlueBuild et apparaît dans le menu d'applications KDE.

L'intégration graphique au véritable panneau Plasma reste une étape distincte. Elle nécessitera une sauvegarde de la disposition existante, une confirmation explicite et une validation sur Bazzite KDE avant activation.

## Centre de notifications LEOS — première alpha

`notification_store.py` conserve un historique local privé, borné à 100 événements, avec niveaux info/succès/avertissement/erreur, état lu/non lu, suppression individuelle et effacement global. Les données sont validées, écrites atomiquement et protégées en permissions 0700/0600. `notification_model.py`, `qml/Notifications.qml` et `notifications_main.py` fournissent une interface Qt Quick autonome, installée dans le menu d'applications KDE par `leos-notifications.desktop`.

**Périmètre explicite :** ce centre affiche les événements émis par les composants LEOS via `NotificationModel.addNotification` ou `desktop.notifications.post_notification`. Il ne capture ni ne remplace l'historique des notifications système KDE : Plasma reste responsable des notifications natives.

La boutique publie désormais les résultats des opérations Flatpak (installation, désinstallation, vérification échouée, inventaire indisponible et erreurs d'exécution). Le Centre de contrôle publie les résultats d'application/restauration des schémas de couleurs KDE, des Plasma Styles et de création des sauvegardes Plasma. Les préférences ordinaires ne génèrent pas de notification afin d'éviter le bruit.

Le stockage recharge l'historique sous verrou interprocessus avant chaque modification afin de tenir compte des événements écrits par d'autres processus LEOS sans perdre les écritures concurrentes. Le verrou et les fichiers restent privés. Un fichier invalide ou inaccessible n'est pas écrasé lors de l'ajout d'un événement. Les composants restent fonctionnels même si l'historique est indisponible : l'échec d'enregistrement ne bloque jamais une installation ou un réglage.


## Lancement des applications

Le menu lit les champs `Exec` des fichiers Desktop Entry et développe explicitement les codes freedesktop pris en charge (`%c`, `%i`, `%k`, `%%`). Les placeholders de fichiers/URL sont omis lorsqu'aucun document n'est associé au lancement. Les codes inconnus ou mal placés sont refusés. Le champ `Path` est résolu vers un dossier absolu existant ; les entrées avec un dossier de travail invalide sont ignorées. Les arguments sont transmis à `QProcess.startDetached` sans interprétation par un shell.

Le menu masque aussi les entrées `Terminal=true` tant qu'aucun terminal n'est intégré à son flux de lancement, et respecte `TryExec` lorsqu'il est défini.


### Icônes du menu Desktop

Les cartes du menu utilisent les noms d'icônes déclarés dans les fichiers
`.desktop`. Un fournisseur QML interroge le thème d'icônes KDE via `QIcon`,
accepte également un chemin d'icône local et utilise une icône système générique
si l'icône demandée est absente. Aucun paquet ni thème d'icônes supplémentaire
n'est installé ou sélectionné par LEOS.


Le catalogue respecte aussi les listes `OnlyShowIn` et `NotShowIn` pour
l'environnement actif (`XDG_CURRENT_DESKTOP`, KDE par défaut) et privilégie
les entrées localisées `Name[fr_FR]` / `Name[fr]` et `Comment[fr_FR]` /
`Comment[fr]` selon la locale système.


### Applications récemment utilisées

Le menu conserve jusqu'à 20 identifiants de fichiers `.desktop` dans
`$XDG_STATE_HOME/leos/recent-applications.json` (par défaut
`~/.local/state/leos/recent-applications.json`). L'historique est écrit
atomiquement, protégé par un verrou et des permissions privées. Il ne contient
ni commandes de lancement ni chemins privés. Seuls les lancements confirmés
par `QProcess.startDetached` sont enregistrés ; un échec d'écriture n'empêche
pas l'application de démarrer. Les entrées supprimées du système disparaissent
simplement de la vue, sans effacer les autres éléments de l'historique.


### Résolution XDG et ordre des favoris

Le catalogue parcourt récursivement les répertoires `applications/` définis par
`XDG_DATA_HOME` et `XDG_DATA_DIRS`. Les chemins imbriqués sont convertis en
identifiants freedesktop en remplaçant les séparateurs par des tirets
(`vendor/tools/editor.desktop` devient `vendor-tools-editor.desktop`).
La priorité XDG est résolue avant la lecture des fichiers : une entrée
utilisateur `Hidden=true` masque donc bien la version système de même
identifiant. Les collisions d'identifiants suivent la priorité des répertoires,
et chaque application n'apparaît qu'une fois dans le catalogue.

Dans la catégorie Favoris, les commandes haut/bas déplacent une entrée d'une
position à la fois. Elles sont masquées hors de cette catégorie et désactivées
pendant une recherche pour éviter un ordre ambigu. L'étoile capture l'état
précédent avant la mise à jour du modèle afin d'afficher le bon retour
« ajouté » ou « retiré ». Le menu se ferme après un lancement accepté et avec
Échap ; un lancement refusé laisse le menu ouvert et conserve l'erreur précise
du backend.
