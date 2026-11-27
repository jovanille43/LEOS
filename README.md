# LEOS 🦁

**LEOS** est une distribution Linux personnalisée basée sur **Bazzite KDE**. Son objectif est de réunir une expérience de bureau élégante et un environnement gaming immersif au sein d'un seul système.

> **État au 27 novembre 2026 :** la PR #73 est fusionnée dans `main` (`dc1faf7`). Les contrôles Python et BlueBuild de ce commit sont réussis ; la reconstruction des trois images est encore en cours et aucune ISO issue de ce commit n'est donc déclarée disponible à ce stade. Le dernier lot complet prouvé est le run ISO [#45855325068](https://github.com/jovanille43/LEOS/actions/runs/45855325068), basé sur `dcd8966` : les trois ISO (standard, NVIDIA legacy et NVIDIA open) ont été générées, vérifiées (checksum/digest/provenance) et démarrées jusqu'à l'accueil Anaconda WebUI sous UEFI/QEMU. Ce smoke test ne réalise pas une installation complète. La dernière installation interactive confirmée en VM remonte au 20 novembre et concernait un commit antérieur (`3c97827`). LEOS reste donc en validation : il faut réinstaller l'ISO du commit courant et contrôler le parcours Desktop/Gaming avant toute diffusion.

## Vision

LEOS propose deux expériences au sein d'une seule installation :

- **Desktop Mode** — bureau KDE personnalisé, avec l'emblème LEOS représentant le lion seul.
- **Gaming Mode** — application LEOS plein écran au-dessus de KDE, pensée pour la manette, avec l'emblème du lion tenant une manette.

Les deux modes partagent le même système, les mêmes fichiers, applications, pilotes et services. Le passage d'un mode à l'autre se fait sans redémarrage. À chaque transition vers Gaming ou retour vers Desktop, LEOS demande une confirmation ; les applications ouvertes restent en arrière-plan et ne sont jamais fermées automatiquement.

## Identité visuelle

L'identité LEOS repose sur un lion métallique, une typographie dédiée, une base sombre et un dégradé A/B librement choisi au premier démarrage. Aucune paire de couleurs n'est imposée.

- Desktop : emblème officiel du lion seul.
- Gaming : emblème officiel du lion avec manette.
- Les animations et sons LEOS sont configurables indépendamment et peuvent être désactivés.

Les références visuelles fournies pour le projet doivent être respectées. L'image comparative des deux emblèmes sert de référence et ne doit pas devenir le visuel principal d'un écran.

## Base technique

| Élément | Choix |
| --- | --- |
| Système de base | Bazzite KDE Desktop |
| Construction de l'image | BlueBuild |
| Interface Gaming | Qt 6 / QML avec logique applicative PySide6 |
| Interface Desktop | KDE Plasma personnalisé |
| Gestion des manettes | Linux evdev via python3-evdev |
| Dépôt | GitHub |
| Distribution visée | Image LEOS dédiée, puis ISO installable |

LEOS conserve les mécanismes natifs de Bazzite, KDE et Linux. Les composants spécifiques au projet complètent cette base sans créer de gestionnaires concurrents ni contourner le modèle immuable de Bazzite.

### Compatibilité matérielle

LEOS vise un large éventail de PC x86_64 démarrant en UEFI, sans configuration CPU/GPU imposée. La compatibilité Gaming dépend notamment de Vulkan, des pilotes et des périphériques. La base Bazzite publie comme référence un quadricœur 2 GHz, 8 Go de RAM, un GPU Vulkan 1.3+ et 50 Go libres sur SSD interne (120 Go recommandés). Trois variantes matérielles du même système ont été construites, publiées et signées : `leos` (AMD/Intel), `leos-nvidia` (NVIDIA Maxwell/Pascal/Volta) et `leos-nvidia-open` (NVIDIA Turing et plus récent). Les trois ISO correspondantes ont été générées dans le run [#45855325068](https://github.com/jovanille43/LEOS/actions/runs/45855325068), sur le commit `dcd8966`, et ont passé le smoke test UEFI/QEMU jusqu'à l'accueil Anaconda. Les ISO du commit courant `dc1faf7` doivent encore être reconstruites puis testées ; les GPU réels restent à valider sur matériel adapté. Voir [la politique de compatibilité matérielle](docs/hardware-compatibility.md) et le [guide d'installation](docs/installation.md).

### Composants source présents dans le dépôt

- **Gaming Mode** : bibliothèque locale unifiée avec imports Steam, Heroic (Epic, GOG et Amazon Games), Lutris et playlists RetroArch locales (`.lpl`), ajout manuel, favoris, jeux récents, recherche et navigation clavier/manette. La boutique propose sept émulateurs facultatifs, détectés en natif ou Flatpak. Les playlists RetroArch sont importées et peuvent utiliser le cœur configuré ; les dossiers explicitement sélectionnés peuvent être importés pour Dolphin (GameCube/Wii), PCSX2 (PS2), PPSSPP (PSP), melonDS (DS), Eden (Switch) et RPCS3 (PS3). LEOS ne parcourt jamais les disques à la recherche de ROM.
- **Cohérence de bibliothèque** : titres nettoyés sans réécriture de leur capitalisation, recherche tolérante aux accents et aux espaces répétés, signalement prudent des titres identiques entre sources. Les entrées ne sont jamais fusionnées ou supprimées automatiquement.
- **Métadonnées de jeu** : source, identifiant de catalogue, jaquette locale lorsqu'elle existe et état d'installation vérifié. Les chemins privés et commandes de lancement ne sont pas exposés dans la fiche QML.
- **Télémétrie Gaming** : mesures CPU/RAM et informations GPU/VRAM/température uniquement lorsque les interfaces DRM/hwmon du pilote les exposent. L'overlay FPS repose sur MangoHud s'il est présent ; LEOS n'invente pas de mesures.
- **Sélecteur Desktop/Gaming** : modes au sein d'une seule session KDE, dernier mode mémorisé et navigation par clavier/manette ; les transitions doivent encore être validées en session réelle.
- **Centre de contrôle LEOS** : pages matériel et connexions, diagnostic système avec rapport de support expurgé, nettoyage avec aperçu, mises à jour, notifications et réseau. Les inventaires matériels et diagnostics sont en lecture seule ; les réglages système s'appuient sur les outils natifs.
- **Centre des notifications LEOS** : historique local des événements émis par les composants LEOS. Les notifications système natives et leur historique restent gérés par Plasma ; les événements LEOS en Gaming sont conservés silencieusement pour ne pas interrompre une partie.
- **Centre des manettes** : détection, test des boutons/axes et profils de navigation LEOS, sans modifier globalement les mappings Linux ou ceux des jeux externes.
- **Boutique LEOS** : catalogue curaté, recommandations issues d'une liste réellement installable, inventaire Flatpak utilisateur/système et confirmation avant toute opération. Les mises à jour ciblées vérifient l'origine Flathub de l'application et du dépôt, puis recontrôlent cette origine après confirmation ; LEOS ne lance pas de mise à jour globale depuis la fiche d'une application. Ces opérations restent à tester sur une session Bazzite réelle.
- **Premier démarrage** : le sélecteur présente Desktop et Gaming. Le choix des accents A/B est obligatoire. Au premier choix de Desktop, le parcours propose d'activer le profil visuel LEOS (fond officiel, couleurs, Plasma Style, icônes LEOS et dock), avec le focus initial sur cette action recommandée, après inspection et sauvegarde de la configuration Plasma ; l'utilisateur peut aussi choisir explicitement de conserver son bureau actuel. Un état en trois étapes indique l'identité A/B, le guide et l'état du profil Desktop. Les applications Brave, LibreOffice et VLC sont proposées séparément et ne sont installées qu'après confirmation.
  Détails : [guide du premier démarrage](docs/first-run.md).
- **Validation continue** : workflows GitHub Actions pour compiler les sources Python, exécuter les tests et contrôler la recette BlueBuild.

Les composants du commit `dcd8966` sont intégrés aux trois images et aux trois ISO du run #45855325068. Les améliorations de la PR #73 sont présentes dans les sources `main` (`dc1faf7`) mais attendent la fin de la reconstruction des images et une nouvelle génération ISO. Les tests automatisés et le smoke test UEFI/QEMU ne remplacent pas une installation interactive, la validation des interfaces dans Plasma ni les essais sur PC physique.

## Gaming Mode

- Application LEOS plein écran au-dessus de KDE ; KDE reste actif en arrière-plan.
- Interface utilisable à la manette, au clavier et à la souris.
- Bibliothèque locale organisée en catégories PC Gaming, Nintendo, PlayStation, SEGA et Arcade. Les playlists RetroArch locales alimentent les catégories Nintendo, PlayStation, SEGA et Arcade. La boutique propose sept émulateurs installables à la demande ; ils ne sont pas préinstallés dans l'image. Les playlists RetroArch et les dossiers de jeux explicitement choisis alimentent la bibliothèque et les parcours de lancement pris en charge, sans scan global des disques.
- Recherche par titre, plateforme ou source, insensible à la casse et aux accents, et tolérante aux espaces répétés.
- Favoris et historique des jeux récemment lancés, conservés dans le profil utilisateur.
- Navigation clavier et manette, avec confirmation/retour et commandes adaptées aux profils contrôleur pris en charge.
- Imports Steam (bibliothèques principales et secondaires), Heroic (Epic, GOG et Amazon Games), Lutris et playlists RetroArch locales ; ajout manuel de commandes de lancement. La présence des sept émulateurs (RetroArch, Dolphin, PCSX2, PPSSPP, melonDS, RPCS3 et Eden) est détectée en lecture seule (installation native ou Flatpak) et affichée dans le panneau rapide. Les dossiers de jeux ne sont parcourus qu'après sélection explicite ; les montages Flatpak sont limités en lecture aux emplacements requis.
- Jaquettes recherchées dans les caches locaux Steam/Lutris et les fichiers explicitement référencés par Heroic. Aucune image distante n'est téléchargée.
- Fiche de jeu : titre, plateforme, source, statut des fichiers locaux et identifiant catalogue ; chemins privés et arguments de lancement restent masqués.
- Signalement des doublons potentiels par correspondance exacte de titre normalisé. Les éditions sont préservées et aucune entrée n'est fusionnée ou supprimée.
- Panneau rapide, statistiques système réelles et profils d'énergie natifs disponibles lorsque les services matériels correspondants existent.
- MangoHud peut être ajouté aux commandes de lancement direct lorsqu'il est installé et activé. LEOS ne présente pas de compteur FPS interne fictif.
- Les introductions vidéo Desktop/Gaming sont raccordées à Qt Multimedia, avec son intégré, réglage sonore indépendant et repli en cas d'erreur. Les trois vidéos sont présentes dans `branding/animations/` (Desktop en MOV, Gaming en MP4) ; leur décodage et leur restitution audio doivent encore être validés sur Bazzite. L'intégration en source couvre les playlists RetroArch (avec cœur lorsqu'il est configuré), ainsi que les imports et commandes de lancement pour Dolphin, PCSX2, PPSSPP, melonDS, Eden et RPCS3 depuis des dossiers explicitement choisis. Les essais de lancement, les assistants BIOS/firmware pour les autres émulateurs et le stockage externe restent à valider sur Bazzite. Voir [l'état de l'intégration des émulateurs](docs/emulator-integration.md).

## Desktop Mode

- Bureau KDE personnalisé avec l'identité LEOS ; le premier choix de Desktop propose l'activation du profil officiel après confirmation.
- Profil Desktop LEOS : fond sombre et emblème officiel, dégradé A/B choisi par l'utilisateur, Plasma Style et icônes LEOS assortis, et dock inférieur centré. Une sauvegarde Plasma est créée avant l'application ; les configurations multi-panneaux restent intactes.
- Menu principal LEOS avec recherche, catégories, favoris et applications récemment utilisées. Les favoris LEOS disponibles sont proposés sur le dock.
- Notifications natives et historique système restent gérés par Plasma ; le Centre LEOS conserve uniquement les événements émis par les applications et services LEOS.
- Centre de contrôle simplifié pour les fonctions propres à LEOS, avec tableau de bord matériel en lecture seule et accès direct aux paramètres KDE avancés.
- Les fonds d'écran Desktop et Gaming 4K sont fournis ; les transitions Desktop/Gaming utilisent les animations officielles avec piste audio configurable. Leur rendu SVG avec JPEG liés et la restitution vidéo/audio doivent encore être validés sur une session Bazzite réelle.

## Compatibilité matérielle et philosophie universelle

LEOS est conçu pour être installé sur une large gamme de PC modernes compatibles, et non pour une configuration matérielle de référence. Aucun modèle de processeur, de carte graphique, de carte mère, de quantité de RAM ou de SSD précis ne doit être imposé par le projet.

Principes obligatoires :
- Cibler les PC x86_64 modernes compatibles avec la base Bazzite et son processus d'installation ; ne pas promettre la prise en charge de machines qui ne satisfont pas ses prérequis.
- Prendre en charge les plateformes AMD et Intel, ainsi que les GPU AMD, Intel et NVIDIA via les variantes d'image et pilotes adaptés de la base Bazzite lorsque cela est nécessaire.
- Ne jamais coder en dur un modèle de CPU/GPU, une résolution, un nombre d'écrans, un chemin de périphérique ou une quantité de mémoire.
- Détecter les capacités réellement disponibles à l'exécution ; masquer ou désactiver proprement une fonction indisponible sans empêcher le démarrage du bureau.
- Conserver des solutions de repli pour les fonctions optionnelles (télémétrie GPU, MangoHud, Bluetooth, manettes, accélération graphique et effets visuels).
- Ne pas exiger de GPU dédié pour Desktop Mode. Les performances de Gaming Mode dépendent naturellement du matériel et des pilotes présents.
- Garder les applications LEOS indépendantes des outils propriétaires et des interfaces spécifiques à un seul fabricant, sauf intégration facultative et vérifiée.

La compatibilité sera validée progressivement sur une matrice de machines physiques et virtuelles : graphiques intégrés Intel/AMD, GPU AMD dédié, GPU NVIDIA avec sa variante Bazzite adaptée, portables hybrides, écrans simples et multiples, Wi-Fi/Bluetooth et différentes générations de contrôleurs. Une validation sur un PC ne sera jamais présentée comme une garantie universelle.

**Objectif produit :** un seul LEOS, une même expérience Desktop/Gaming, avec une image de base et des variantes matérielles clairement documentées si la prise en charge des pilotes l'exige. Aucun PC de référence unique ne définit les prérequis de LEOS.

## Bluetooth

Le Bluetooth est pris en charge comme fonctionnalité attendue dans Desktop Mode et Gaming Mode : manettes, casques, écouteurs, enceintes, claviers et souris compatibles. LEOS réutilise la pile BlueZ, les paramètres KDE et PipeWire de Bazzite ; il ne lance pas de gestionnaire parallèle. Le Centre de contrôle offrira un accès rapide, tandis que l'association et le dépannage complets resteront accessibles dans KDE. Le Gaming Mode ne désactivera pas le Bluetooth lors d'un changement de mode. La validation sur matériel réel reste à effectuer ; voir [docs/bluetooth.md](docs/bluetooth.md).

## Centre des manettes

Le Centre des manettes propose une vue des contrôleurs détectés par Linux, un test des boutons et axes analogiques, la détection automatique des profils Xbox/PlayStation/Nintendo lorsqu'elle est fiable, le choix manuel d'un profil, le réglage d'une zone morte et l'enregistrement de la position neutre des axes.

Les préférences sont enregistrées dans le compte Linux de l'utilisateur et appliquées à la navigation de l'interface Gaming LEOS (profil, zone morte et calibration des sticks). Le prototype ne modifie pas les mappings du système ou des jeux externes : les configurations Steam et des lanceurs restent prioritaires.

## Applications fournies et boutique LEOS

Après la sélection de Desktop Mode, le lanceur peut proposer Brave, LibreOffice et VLC dans une fenêtre de consentement KDE. Rien n'est installé sans acceptation explicite. L'offre est mémorisée après acceptation complète ou refus ; en cas d'échec partiel, seules les applications manquantes pourront être retentées. Une désinstallation ultérieure depuis la boutique n'entraîne pas de réinstallation automatique. Steam est déjà fourni par la base Bazzite Desktop. La boutique distingue les applications utilisateur et système : les deux peuvent être désinstallées depuis la boutique après confirmation ; les applications système peuvent demander une authentification administrateur. Les composants RPM/OSTree constitutifs de Bazzite restent gérés par les outils système.

La boutique propose jeux, émulateurs, applications, utilitaires et éléments de personnalisation. La première sélection V2 comprend RetroArch, Dolphin, PCSX2, PPSSPP, melonDS, RPCS3 et Eden depuis Flathub ; chaque installation reste facultative et exige une confirmation. Elle s'appuie sur Flatpak/Flathub, les mécanismes natifs de Bazzite et les intégrations de lanceurs compatibles.

**Toute installation ou désinstallation exige une confirmation explicite.** Chaque fiche doit préciser le contenu de l'opération, sa source, sa compatibilité et ses éventuelles dépendances.

## Principes de sécurité et de fiabilité

- Aucune installation ou désinstallation sans confirmation.
- Aucune fermeture d'application sans choix explicite de l'utilisateur lors d'une transition.
- Les mises à jour utilisent les mécanismes natifs de Bazzite ; l'utilisateur décide de leur installation.
- Les opérations de nettoyage, suppression ou modification système demandent une confirmation.
- Les limites de compatibilité matérielle et logicielle sont indiquées clairement.

## Structure du dépôt

```text
LEOS/
├── .github/workflows/   # Automatisation et vérifications
├── branding/            # Logos, animations, sons et ressources
├── files/config/        # Configuration partagée de LEOS
├── controller_center/   # Gestion et test des manettes
├── control_center/      # Paramètres LEOS
├── desktop/             # Personnalisation du Desktop Mode
├── docs/                # Architecture et documentation
├── gaming/              # Application Gaming LEOS
├── shop/                # Boutique LEOS et opérations Flatpak confirmées
├── recipes/             # Recette BlueBuild
└── README.md
```

## Prochaines étapes

1. **Installer l'ISO issue de `dc1faf7` en VM UEFI** — après publication du nouveau lot, vérifier SHA-256 et digest, installer uniquement sur un disque QCOW2 dédié, créer le compte et contrôler l'ouverture de session.
2. **Valider l'expérience de première session** — vérifier le choix A/B, l'activation du profil Desktop, le fond, le dock, le menu, le Centre de contrôle, Gaming plein écran, les deux transitions et la persistance après redémarrage.
3. **Corriger les anomalies d'installation ou de session** — traiter les blocages réels et relancer les contrôles automatiques.
4. **Valider sur matériel adapté** — tester les variantes GPU AMD/Intel et NVIDIA, puis réseau, audio, Bluetooth, manettes, veille, écrans et rollback.
5. **Valider le Gaming plug-and-play** — tester les opérations Flatpak réelles, les imports/lancements de jeux, les assistants BIOS/firmware et les bibliothèques externes, sans annoncer comme certifiées les fonctions non testées.

## État actuel

- [x] Architecture commune Bazzite KDE / BlueBuild et deux modes au sein d'une seule session.
- [x] Prototypes source du sélecteur, Gaming, Desktop, Centre de contrôle, Centre des manettes, boutique et notifications.
- [x] Imports de bibliothèque Steam, Heroic et Lutris, ajout manuel, favoris, récents et navigation manette.
- [x] Trois emblèmes JPEG présents dans le dépôt et identiques aux originaux reçus ; trois vidéos hébergées, contrôlées et décodables (leurs empreintes diffèrent des vidéos sources transmises).
- [x] Transitions vidéo via Qt Multimedia avec piste audio configurable et repli en cas d'erreur.
- [x] Contrôles Python, lint QML Qt 6, décodage des vidéos, validation/génération de la recette BlueBuild et contrôle SHA-256 des huit ressources déployées réussis sur GitHub Actions.
- [x] Fonds d'écran Desktop et Gaming 4K empaquetés, avec aperçus dans le Centre de contrôle et accès aux paramètres natifs KDE ; le rendu SVG et l'application réelle restent à valider sur Bazzite.
- [x] Application guidée du dock à un panneau unique, sauvegarde préalable, confirmation et refus sûr des dispositions multi-panneaux ; validation sur Bazzite encore nécessaire.
- [x] Préparation automatique de Heroic et des sept émulateurs Flatpak dans le profil utilisateur à la première session connectée, après consentement ; imports et lancement des titres pris en charge pour Dolphin, PCSX2, PPSSPP, melonDS, Eden et RPCS3 depuis des dossiers explicitement choisis.
- [x] Import des playlists RetroArch avec résolution du cœur propre à l'entrée ou du cœur par défaut lorsque disponible.
- [ ] Valider les installations, mises à jour et lancements Flatpak sur Bazzite réel, les assistants, les supports externes et la reconnexion après retrait.
- [x] Construire, publier et signer les trois images conteneur Bazzite : standard, NVIDIA legacy et NVIDIA open.
- [x] Générer les trois ISO (standard, NVIDIA legacy et NVIDIA open) avec checksum, digest source, manifeste de provenance et smoke test UEFI/QEMU jusqu'à Anaconda WebUI — run #45855325068, commit `dcd8966`.
- [ ] Répéter la construction des trois images et des trois ISO après la fusion de la PR #73 (`dc1faf7`) ; le build d'images est en cours à la date de cet état.
- [x] Ajouter `cosign.pub` et configurer les secrets GitHub `SIGNING_SECRET` et `COSIGN_PASSWORD` pour la signature chiffrée.
- [x] Construire, publier et signer les images conteneur LEOS avec Cosign.
- [x] Vérifier le démarrage UEFI/QEMU de l'installateur et l'apparition de l'accueil Anaconda WebUI ; ce contrôle n'effectue pas l'installation sur disque.
- [ ] Installer l'ISO issue du commit courant en VM, valider le parcours post-installation et tester ensuite sur matériel physique.

**État de livraison :** les trois ISO du commit `dcd8966` sont disponibles comme artefacts du run [#45855325068](https://github.com/jovanille43/LEOS/actions/runs/45855325068). Les sources plus récentes de `dc1faf7` contiennent les améliorations de la PR #73, mais leur nouvelle chaîne de build/ISO doit se terminer avant de fournir un artefact correspondant. Aucune version taguée ni GitHub Release n'a été publiée. La validation interactive en VM et la validation matérielle restent requises. Voir [le guide de validation en machine virtuelle](docs/virtual-machine-validation.md) et [la checklist matérielle](docs/hardware-validation.md).

## Contribuer, licences et publications

- [Guide de contribution](CONTRIBUTING.md)
- [Licence du code](LICENSE) — GPL-3.0-or-later
- [Périmètre des licences des ressources](ASSET-LICENSING.md) — les médias et éléments de marque ne sont pas automatiquement couverts par la licence du code.
- [Journal des modifications](CHANGELOG.md)
- [Processus de release versionnée](docs/release-process.md)
- [Signature et vérification Cosign](docs/signing.md)
- [Entretien et gouvernance GitHub](docs/github-maintenance.md)

Aucune version taguée ni GitHub Release n'a encore été publiée. La première préversion ne sera préparée qu'après les validations VM et matérielles décrites dans le processus de release.

---

*LEOS — One system. Two experiences.*
