# Intégration des émulateurs — LEOS V2

## Objectif

Faire des émulateurs une fonction de première classe de LEOS : préparer automatiquement les outils, importer les bibliothèques locales compatibles, afficher les jeux dans Gaming, lancer à la manette et indiquer clairement les prérequis restants. La présence d'une fiche dans la boutique ne doit jamais être présentée comme une intégration terminée.

## État vérifié de départ

- La bibliothèque LEOS importe les manifestes Steam, Heroic, Lutris et les playlists RetroArch locales `.lpl`.
- Elle ne réalise aucun scan global de ROM : seuls les dossiers explicitement sélectionnés par l'utilisateur sont parcourus.
- Au premier démarrage d'une session KDE, LEOS lance en tâche de fond un bootstrap Flatpak à usage utilisateur ; il installe Heroic et les six émulateurs listés ci-dessous si Internet et Flathub sont disponibles.
- Le bootstrap enregistre un marqueur uniquement lorsque les sept applications sont vérifiées comme installées. En cas d'échec, il réessaie à la prochaine connexion ; après succès, il respecte les désinstallations ultérieures et ne réinstalle pas les applications supprimées par l'utilisateur.
- Steam et Lutris sont fournis par l'image Bazzite de base ; LEOS n'en installe pas une seconde copie.
- La boutique garde la possibilité de réinstaller manuellement une application après confirmation.
- Les BIOS, firmwares, clés, jeux et cœurs ne sont ni inclus ni téléchargés par LEOS.

## Outils préparés automatiquement par LEOS

| Application | Plateforme | Identifiant Flathub | Remarque |
| --- | --- | --- | --- |
| Heroic Games Launcher | Epic / GOG / Amazon | `com.heroicgameslauncher.hgl` | Lanceur PC ; les comptes et la compatibilité de chaque jeu restent à configurer |
| RetroArch | Multi-systèmes | `org.libretro.RetroArch` | Paquet vérifié par Flathub ; les cœurs restent gérés séparément dans RetroArch |
| Dolphin | GameCube / Wii | `org.DolphinEmu.dolphin-emu` | Paquet Flathub communautaire non vérifié par le projet amont |
| PCSX2 | PlayStation 2 | `net.pcsx2.PCSX2` | Paquet publié au nom de PCSX2 Team |
| PPSSPP | PSP | `org.ppsspp.PPSSPP` | Paquet publié par le projet PPSSPP |
| melonDS | Nintendo DS / DSi | `net.kuribo64.melonDS` | Paquet vérifié Flathub ; l'import des ROM Nintendo DS est relié à Gaming, les prérequis BIOS/firmware restent à renseigner |
| RPCS3 | PlayStation 3 | `net.rpcs3.RPCS3` | Paquet Flathub communautaire non vérifié par le projet amont |

Heroic et les six émulateurs sont installés automatiquement dans le profil de l'utilisateur, jamais dans l'image système ni avec les droits administrateur. La première session nécessite une connexion Internet. Si l'installation échoue, LEOS la retente à la prochaine connexion ; une fois le lot terminé, une désinstallation volontaire est respectée. Les paquets Flathub communautaires non vérifiés restent clairement identifiés dans la boutique.

## Étapes d'intégration

### V2-A — Catalogue et installation automatique

- [x] Ajouter les six fiches dans la catégorie Émulation de la boutique.
- [x] Utiliser les identifiants d'applications Flathub du catalogue et distinguer les paquets vérifiés des paquets communautaires.
- [x] Indiquer les limites des paquets communautaires.
- [x] Préciser que jeux, BIOS, firmwares et cœurs ne sont pas fournis.
- [x] Ajouter un bootstrap utilisateur automatique, avec contrôle de Flathub, vérification après installation, reprise après échec et respect des désinstallations ultérieures.
- [ ] Tester réellement l'installation des sept applications sur Bazzite/LEOS avec réseau disponible et indisponible.

### V2-B — Détection des émulateurs installés

- [x] Détecter les déploiements Flatpak utilisateur et système via les dossiers d'applications effectivement déployés.
- [x] Détecter les exécutables natifs connus pour les six émulateurs de la sélection et le lanceur Heroic.
- [x] Afficher dans le panneau rapide Gaming l'état « disponible » ou « non détecté », avec le type d'installation lorsqu'elle est trouvée.
- [x] Garder la détection strictement en lecture seule : aucun scan ROM, aucune installation et aucun lancement pendant la détection.
- [ ] Distinguer la configuration d'un émulateur (BIOS/firmware/cœurs) de sa seule présence.
- [ ] Ajouter des tests fonctionnels d'installation et de lancement sur Bazzite réel.

La présence d'un exécutable ou d'un déploiement Flatpak confirme uniquement que l'application est détectée. Elle ne certifie ni la configuration, ni la disponibilité d'un BIOS/firmware, ni la capacité à lancer un titre.

### V2-C — Import facultatif des jeux

- [x] Permettre à l'utilisateur de sélectionner explicitement un dossier depuis Gaming Mode avec un navigateur LEOS natif, contrôlable au D-pad et au clavier (haut/bas : parcourir, droite/A : entrer, gauche : parent, Menu : utiliser le dossier courant).
- [x] Afficher uniquement les sous-dossiers immédiats visibles, dans une liste triée et limitée à 256 entrées par niveau ; le navigateur refuse les liens symboliques, les chemins traversants et les entrées cachées.
- [x] Démarrer dans le dossier personnel, permettre de remonter au parent, et refuser de choisir la racine système ou le dossier personnel entier comme bibliothèque de jeux.
- [x] Mémoriser les chemins choisis dans la configuration privée LEOS.
- [x] Scanner uniquement ce dossier et ses sous-dossiers, avec limites de profondeur, d'entrées et de jeux ; ignorer fichiers cachés et liens symboliques.
- [x] Ajouter les imports de fichiers pour Dolphin (GameCube/Wii), PCSX2 (PS2), PPSSPP (PSP) et melonDS (Nintendo DS), avec filtres d'extensions dédiés et lancement melonDS en plein écran.
- [x] Construire les commandes de lancement en arguments séparés, sans shell, et accorder uniquement un accès Flatpak en lecture au dossier sélectionné.
- [x] Revalider l'existence du fichier, son appartenance au dossier choisi et la disponibilité de l'émulateur juste avant le lancement.
- [ ] Ajouter les parcours d'import et de lancement pour RPCS3 et les cœurs RetroArch ; ne pas activer un profil tant que ses arguments et prérequis ne sont pas vérifiés.
- [ ] Ajouter la gestion UI de retrait des dossiers mémorisés et valider les montages externes.

Les jeux ne sont jamais modifiés, déplacés, renommés ou supprimés. Les éditions restent séparées ; les doublons potentiels ne sont ni fusionnés ni supprimés automatiquement.

### V2-D — Lancement sécurisé et sandbox

- [x] Dolphin : transmettre le fichier au paramètre `-e`.
- [x] PCSX2 : lancer en plein écran et séparer les options du chemin avec `--`.
- [x] PPSSPP : transmettre directement le fichier de jeu à l'application.
- [x] melonDS : transmettre une ROM Nintendo DS en argument et demander le plein écran (`-f`).
- [x] Construire chaque lancement comme une liste d'arguments explicites ; aucun shell ni commande issue d'un nom de fichier.
- [x] Pour Flatpak, n'accorder qu'un accès en lecture au dossier choisi ; aucun accès global au dossier personnel n'est ajouté.
- [x] Revalider l'existence du fichier, son appartenance au dossier choisi et la disponibilité de l'émulateur immédiatement avant le lancement.
- [ ] Tester le lancement et le retour au Gaming Mode sur Bazzite réel, avec manette et jeux sur stockage externe.

### V2-E — BIOS, firmware et cœurs

- Ne jamais distribuer, extraire d'une console ou télécharger des BIOS, firmware, clés ou fichiers protégés.
- Expliquer dans l'assistant de configuration que l'utilisateur doit fournir les fichiers qu'il est autorisé à utiliser.
- Vérifier uniquement la présence locale lorsqu'un format et un emplacement sont documentés ; ne pas téléverser ni lire le contenu privé.
- RetroArch garde la gestion de ses cœurs dans son environnement ; aucune installation automatique de cœur sans une action explicite et documentée.

### V2-F — Validation

- Tests unitaires des identifiants Flatpak, profils de plateformes, extensions, chemins, liens symboliques, limites de scan et commandes de lancement.
- Tests de non-régression Steam/Heroic/Lutris/RetroArch.
- Essais en VM pour l'interface, puis sur matériel réel pour Vulkan, performances, contrôleurs et audio.
- Une fonction ne devient « validée » qu'après un essai réel documenté ; les tests structurels ne suffisent pas.

## Critère de disponibilité V2

L'intégration Gaming des émulateurs ne sera déclarée terminée que lorsque l'utilisateur pourra installer un émulateur depuis la boutique, choisir un dossier de jeux, voir ses titres pris en charge dans la bibliothèque, connaître clairement les prérequis manquants et lancer un jeu sans sortie de la session LEOS ni accès disque excessif.


## Références techniques amont

Les formats et options de lancement de la première intégration s'appuient sur les documentations et interfaces des projets :

- **Dolphin — formats de dumps** : https://dolphin-emu.org/docs/faq/
- **Dolphin — arguments de ligne de commande** : https://github.com/dolphin-emu/dolphin/blob/master/Readme.md
- **PCSX2 — options CLI** : https://pcsx2.net/docs/advanced/cli/
- **PCSX2 — filtre des fichiers de jeu accepté par l'interface** : https://github.com/PCSX2/pcsx2/blob/master/pcsx2-qt/MainWindow.cpp
- **PPSSPP — formats de jeux et copies personnelles** : https://www.ppsspp.org/getgames/
- **PPSSPP — arguments de ligne de commande** : https://www.ppsspp.org/docs/reference/command-line/
- **melonDS — argument ROM et option plein écran** : https://melonds.kuribo64.net/board/thread.php?id=924
- **melonDS — préchargement des ROM dans l'interface Qt** : https://github.com/melonDS-emu/melonDS/blob/master/src/frontend/qt_sdl/main.cpp

Lors de toute évolution des formats ou des arguments, mettre à jour les tests de contrat et revérifier les options sur les versions Flatpak réellement prises en charge. La liste déclarée par un projet amont ne remplace pas les essais de lancement sur Bazzite.
