# Intégration des émulateurs — LEOS V2

## Objectif

Faire des émulateurs une fonction de première classe de LEOS : installation facultative dans la boutique, détection explicite des jeux de l'utilisateur, affichage dans la bibliothèque Gaming, lancement à la manette et état clair des prérequis. La présence d'une fiche dans la boutique ne doit jamais être présentée comme une intégration terminée.

## État vérifié de départ

- La bibliothèque LEOS importe les manifestes Steam, Heroic, Lutris et les playlists RetroArch locales `.lpl`.
- Elle ne parcourt pas les dossiers de ROM.
- La recette de l'image n'installe aucun émulateur par défaut.
- La boutique peut installer des applications Flatpak depuis Flathub après contrôle de la source et confirmations successives.
- Les BIOS, firmwares, clés, jeux et cœurs ne sont ni inclus ni téléchargés par LEOS.

## Première sélection dans la boutique

| Application | Plateforme | Identifiant Flathub | Remarque |
| --- | --- | --- | --- |
| RetroArch | Multi-systèmes | `org.libretro.RetroArch` | Paquet vérifié par Flathub ; les cœurs restent gérés séparément dans RetroArch |
| Dolphin | GameCube / Wii | `org.DolphinEmu.dolphin-emu` | Paquet Flathub communautaire non vérifié par le projet amont |
| PCSX2 | PlayStation 2 | `net.pcsx2.PCSX2` | Paquet publié au nom de PCSX2 Team |
| PPSSPP | PSP | `org.ppsspp.PPSSPP` | Paquet publié par le projet PPSSPP |
| melonDS | Nintendo DS / DSi | `net.kuribo64.melonDS` | Compatibilité DSi et réseau à qualifier |
| RPCS3 | PlayStation 3 | `net.rpcs3.RPCS3` | Paquet Flathub communautaire non vérifié par le projet amont |

Ces applications sont proposées à la demande ; aucune ne doit être installée silencieusement ni ajoutée à la recette système par défaut à ce stade. Les paquets communautaires non vérifiés doivent rester clairement identifiés dans l'interface.

## Étapes d'intégration

### V2-A — Catalogue et installation facultative

- [x] Ajouter les six fiches dans la catégorie Émulation de la boutique.
- [x] Utiliser les identifiants Flathub vérifiés.
- [x] Indiquer les limites des paquets communautaires.
- [x] Préciser que jeux, BIOS et firmwares ne sont pas fournis.
- [ ] Tester réellement l'installation et le lancement sur Bazzite/LEOS.

### V2-B — Détection des émulateurs installés

- [x] Détecter les déploiements Flatpak utilisateur et système via les dossiers d'applications effectivement déployés.
- [x] Détecter les exécutables natifs connus pour les six émulateurs de la sélection.
- [x] Afficher dans le panneau rapide Gaming l'état « disponible » ou « non détecté », avec le type d'installation lorsqu'elle est trouvée.
- [x] Garder la détection strictement en lecture seule : aucun scan ROM, aucune installation et aucun lancement pendant la détection.
- [ ] Distinguer la configuration d'un émulateur (BIOS/firmware/cœurs) de sa seule présence.
- [ ] Ajouter des tests fonctionnels d'installation et de lancement sur Bazzite réel.

La présence d'un exécutable ou d'un déploiement Flatpak confirme uniquement que l'application est détectée. Elle ne certifie ni la configuration, ni la disponibilité d'un BIOS/firmware, ni la capacité à lancer un titre.

### V2-C — Import facultatif des jeux

- [x] Permettre à l'utilisateur de sélectionner explicitement un dossier depuis Gaming Mode ; les chemins choisis sont mémorisés dans la configuration privée LEOS.
- [x] Scanner uniquement ce dossier et ses sous-dossiers, avec limites de profondeur, d'entrées et de jeux ; ignorer fichiers cachés et liens symboliques.
- [x] Ajouter les imports de fichiers pour Dolphin (GameCube/Wii), PCSX2 (PS2) et PPSSPP (PSP), avec filtres d'extensions dédiés.
- [x] Construire les commandes de lancement en arguments séparés, sans shell, et accorder uniquement un accès Flatpak en lecture au dossier sélectionné.
- [x] Revalider l'existence du fichier, son appartenance au dossier choisi et la disponibilité de l'émulateur juste avant le lancement.
- [ ] Ajouter les parcours d'import et de lancement pour melonDS, RPCS3, les cœurs RetroArch et d'autres plateformes ; ne pas activer un profil tant que ses arguments et prérequis ne sont pas vérifiés.
- [ ] Ajouter la gestion UI de retrait des dossiers mémorisés et valider les montages externes.

Les jeux ne sont jamais modifiés, déplacés, renommés ou supprimés. Les éditions restent séparées ; les doublons potentiels ne sont ni fusionnés ni supprimés automatiquement.

### V2-D — Lancement sécurisé et sandbox

- [x] Dolphin : transmettre le fichier au paramètre `-e`.
- [x] PCSX2 : lancer en plein écran et séparer les options du chemin avec `--`.
- [x] PPSSPP : transmettre directement le fichier de jeu à l'application.
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
