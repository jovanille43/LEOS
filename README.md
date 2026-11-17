# LEOS 🦁

**LEOS est un projet de distribution Linux fondé sur Bazzite KDE.** Il réunit un bureau KDE adapté à l’usage quotidien et une interface Gaming plein écran, dans une seule installation et une seule session système.

> **Statut : prototype en validation.** Les trois images LEOS (standard AMD/Intel, NVIDIA legacy et NVIDIA open) ont été construites et signées dans GHCR. Une première ISO standard a également été générée et signée. Elle n’est pas publiée : les premiers essais physiques n’ont pas abouti, avec un échec du contrôle média puis un échec de l’installateur pendant l’installation des logiciels. La cause n’est pas encore établie ; l’intégrité du fichier téléchargé et la lecture de la clé USB doivent être vérifiées avant tout nouvel essai. Une chaîne d’installation Live fondée sur Titanoboa est en cours de prototypage sur une branche séparée ; elle n’a pas encore produit d’ISO validée. Aucune compatibilité matérielle générale ni installation en dual boot n’est encore certifiée.

[![Python checks](https://github.com/jovanille43/LEOS/actions/workflows/python-checks.yml/badge.svg?branch=feature/custom-two-color-themes)](https://github.com/jovanille43/LEOS/actions/workflows/python-checks.yml)
[![BlueBuild recipe checks](https://github.com/jovanille43/LEOS/actions/workflows/recipe-checks.yml/badge.svg?branch=feature/custom-two-color-themes)](https://github.com/jovanille43/LEOS/actions/workflows/recipe-checks.yml)

---

## Sommaire

- [Le principe](#le-principe)
- [Identité visuelle et thèmes](#identité-visuelle-et-thèmes)
- [Desktop Mode](#desktop-mode)
- [Gaming Mode](#gaming-mode)
- [Applications et boutique](#applications-et-boutique)
- [Compatibilité matérielle](#compatibilité-matérielle)
- [Architecture technique](#architecture-technique)
- [Validation et état du projet](#validation-et-état-du-projet)
- [Construction de l’image et de l’ISO](#construction-de-limage-et-de-liso)
- [Documentation](#documentation)
- [Structure du dépôt](#structure-du-dépôt)

## Le principe

LEOS propose deux expériences complémentaires :

| Mode | Expérience |
| --- | --- |
| **Desktop Mode** | Bureau KDE Plasma pour le travail, la navigation et les applications du quotidien. |
| **Gaming Mode** | Interface LEOS plein écran, conçue pour parcourir une bibliothèque de jeux à la manette, au clavier ou à la souris. |

Les deux modes utilisent la même installation Linux, les mêmes fichiers, les mêmes applications, les mêmes pilotes et les mêmes services. Le passage de l’un à l’autre ne nécessite pas de redémarrage du système.

Chaque transition demande une confirmation. Les applications ouvertes restent en arrière-plan : LEOS ne les ferme pas automatiquement lorsqu’on change de mode.

## Identité visuelle et thèmes

L’identité LEOS s’appuie sur un lion métallique, un fond sombre et les emblèmes propres à chaque interface :

- **Desktop** utilise l’emblème du lion seul.
- **Gaming** utilise l’emblème du lion tenant une manette.

Le joueur peut choisir librement deux couleurs :

- **Couleur A** : première extrémité du dégradé ;
- **Couleur B** : seconde extrémité du dégradé.

Le moteur de thème partage cette paire entre les interfaces LEOS : sélecteur de mode, Desktop, Gaming, menu, Centre de contrôle, notifications, Centre des manettes et boutique. Les couleurs d’accent et les dégradés sont recalculés, tandis que les reflets métalliques neutres du lion sont préservés. Le cyan et le magenta ne sont pas imposés : ce ne sont que des valeurs de départ.

L’utilisateur choisit aussi l’apparence des interfaces LEOS : **Sombre**, **Claire** ou **Automatique**. Le mode automatique passe en clair de 07:00 à 18:59, puis en sombre de 19:00 à 06:59, selon l’heure locale. Ce réglage modifie les surfaces neutres et les couleurs de texte sans changer la paire A-B ni les dégradés de l’identité.

Les emblèmes, fonds d’écran et vidéos d’introduction disposent de variantes recolorées dans le cache du compte utilisateur. Les ressources officielles ne sont pas écrasées. Si une conversion ou une lecture vidéo échoue, LEOS conserve un chemin de repli vers la ressource d’origine.

Le thème LEOS ne change pas silencieusement le thème global de KDE. L’application d’un schéma de couleurs KDE est une action séparée, avec confirmation et possibilité de restaurer le schéma précédent. Le basculement automatique horaire concerne les interfaces LEOS ; l’apparence des applications KDE et des composants Plasma reste synchronisée uniquement après une application explicite du schéma dans les Paramètres KDE.

## Desktop Mode

Desktop Mode conserve **KDE Plasma** comme environnement de bureau. LEOS y ajoute ses applications et ses réglages sans remplacer les composants natifs de Bazzite.

Le code du mode Desktop comprend notamment :

- **Menu LEOS** : recherche d’applications installées, catégories, favoris ordonnés et applications récemment utilisées.
- **Centre de contrôle** : réglages LEOS, informations matérielles, connexions, notifications, mises à jour, outils de diagnostic et page de sauvegarde, restauration et import/export externe des préférences LEOS, avec une sauvegarde séparée des dispositions Desktop.
- **Centre des manettes** : détection des contrôleurs, test des boutons et des axes, profils de navigation et calibration utilisés par l’interface LEOS.
- **Boutique LEOS** : catalogue d’applications et gestion des applications Flatpak avec confirmation.
- **Personnalisation Plasma** : aperçu des fonds d’écran LEOS, profils de disposition et préparation d’un dock. L’application d’une disposition de panneau exige une sauvegarde et une confirmation ; les configurations multi-panneaux non prises en charge sont refusées sans modification.

Les fonds d’écran Desktop et Gaming au format SVG 4K sont inclus dans les ressources. Leur sélection passe par les paramètres KDE ; ils ne remplacent pas automatiquement le fond d’écran personnel.

Le menu LEOS et les réglages propres au projet sont disponibles dans le code source. Le dock, les widgets et les personnalisations Plasma avancées ne doivent pas être considérés comme activés par défaut : leur application réelle reste soumise aux contrôles prévus et à une validation sur une session KDE/Bazzite.

## Gaming Mode

Gaming Mode est une application Qt 6 / QML avec logique applicative PySide6. Elle s’affiche en plein écran au-dessus de KDE, qui reste actif en arrière-plan.

### Bibliothèque de jeux

La bibliothèque rassemble les jeux trouvés dans les catalogues locaux des lanceurs pris en charge :

- **Steam** : bibliothèques principales et secondaires.
- **Heroic** : catalogues locaux Epic Games, GOG et Amazon Games.
- **Lutris** : bibliothèque locale.
- **RetroArch** : playlists locales au format JSON `.lpl`.
- **Ajout manuel** : possibilité d’enregistrer un jeu et sa commande de lancement.

La navigation propose des catégories PC Gaming, Nintendo, PlayStation, SEGA, Arcade et Émulation. Les recherches par titre, plateforme ou source tolèrent les différences de casse, d’accents et les espaces répétés. Les favoris et les jeux récemment lancés sont conservés dans le profil utilisateur.

Les doublons potentiels sont signalés, mais les entrées ne sont jamais fusionnées ou supprimées automatiquement. Les différentes éditions d’un jeu restent distinctes. Les jaquettes sont recherchées dans les caches locaux ou dans les fichiers explicitement référencés par les catalogues ; LEOS ne télécharge pas automatiquement d’images distantes.

### Émulateurs et lancement des jeux locaux

La boutique référence les émulateurs suivants via Flathub :

| Émulateur | Plateforme |
| --- | --- |
| RetroArch | Plusieurs systèmes via les cœurs compatibles |
| Dolphin | GameCube et Wii |
| PCSX2 | PlayStation 2 |
| PPSSPP | PlayStation Portable |
| DuckStation | PlayStation |
| Cemu | Wii U |
| Eden | Nintendo Switch 1 |

La présence d’une fiche dans la boutique ne signifie pas que le lancement automatique de tous les formats est déjà intégré. À ce stade, l’association automatique par extension couvre uniquement un ensemble limité et non ambigu :

| Formats reconnus | Émulateur associé |
| --- | --- |
| `.gcm`, `.wbfs`, `.rvz` | Dolphin |
| `.wua`, `.wuhb`, `.wud`, `.wux` | Cemu |
| `.nsp`, `.xci` | Eden |
| `.cso`, `.zso` | PPSSPP |

L’émulateur doit déjà être installé. LEOS peut détecter les installations Flatpak utilisateur, système et certaines installations système nommées déclarées dans `/etc/flatpak/installations.d/`. Pour les installations nommées reconnues, LEOS transmet explicitement le nom d’installation à Flatpak.

Le lancement transmet le fichier sélectionné à l’application via `flatpak run --file-forwarding` et le portail de documents. LEOS ne lance pas directement les fichiers de jeu, n’installe pas d’émulateur à la volée et n’essaie pas de deviner les formats ambigus. Les formats non couverts — par exemple ISO, CHD, CUE/BIN ou PBP — restent visibles mais nécessitent une association manuelle.

### Dossier de jeux et tri automatique

Le service de session surveille le dossier de téléchargement XDG. Sur un profil neuf, si ce dossier pointe encore vers `~/Downloads` ou `~/Téléchargements`, LEOS le configure sur `~/Jeux`. Un dossier de téléchargement personnalisé est conservé et surveillé à la place.

Après stabilisation d’un téléchargement, les formats reconnus sont rangés dans une arborescence de ce type :

```text
~/Jeux/                         # Dossier de téléchargement
~/Emulation/ROMs/
├── Nintendo/
│   ├── GameCube/
│   ├── Wii/
│   ├── Wii U/
│   └── Switch/
├── PlayStation/
├── SEGA/
└── ...
```

Le tri est volontairement prudent :

- les fichiers reconnus sont déplacés vers le dossier de leur système ;
- les ZIP contenant exactement un jeu reconnu peuvent être extraits ; l’archive d’origine est conservée dans `~/Emulation/.archives` ;
- les archives contenant plusieurs jeux, les formats inconnus et les formats ambigus restent dans le dossier d’arrivée ;
- les liens symboliques ne sont pas suivis et le contenu des ROM n’est pas analysé pour décider de leur système.

LEOS ne fournit ni jeux, ni BIOS, ni firmware, ni clés cryptographiques, ni cœurs RetroArch. L’utilisateur doit posséder les fichiers et les droits nécessaires à leur utilisation.

### Manettes, performances et profils d’énergie

Gaming Mode accepte la navigation au clavier, à la souris et avec les manettes compatibles détectées par Linux. Le mapping utilisé concerne la navigation LEOS ; il ne remplace pas les configurations Steam ou celles des jeux externes.

Le panneau rapide donne accès aux fonctions LEOS disponibles, dont les profils d’énergie natifs lorsqu’ils sont exposés par le système et l’ouverture du Centre des manettes. Les changements de profil d’énergie demandent une confirmation.

Les mesures CPU/RAM et les mesures GPU/VRAM/température ne sont affichées que lorsque les interfaces du système ou du pilote les fournissent. MangoHud peut être utilisé pour l’overlay FPS lorsqu’il est installé et activé. LEOS n’invente pas de valeurs lorsqu’une télémétrie n’est pas disponible.

## Applications et boutique

La boutique LEOS s’appuie principalement sur Flatpak/Flathub et les mécanismes natifs de Bazzite.

- Les installations et désinstallations demandent une confirmation explicite.
- La boutique distingue les applications Flatpak utilisateur et système.
- La source et les informations de compatibilité disponibles sont affichées avant l’opération.
- Le dépôt Flathub est vérifié avant une installation utilisateur.
- Les composants du système de base restent gérés par Bazzite et ses outils natifs.

Après le choix de Desktop Mode au premier démarrage, LEOS peut proposer Brave, LibreOffice et VLC. Cette proposition est facultative : aucune de ces applications n’est installée sans accord explicite.

## Compatibilité matérielle

La cible actuelle est un PC **x86_64 démarrant en UEFI**. LEOS n’est pas lié à un modèle précis de processeur, de carte graphique, de carte mère, de mémoire ou de stockage. La compatibilité dépend toutefois des limites de Bazzite, du noyau Linux, des pilotes et des périphériques de chaque ordinateur. LEOS ne peut donc pas garantir le fonctionnement sur « tous les ordinateurs ».

Trois recettes BlueBuild partagent les mêmes composants LEOS :

| Variante | Base | Cible graphique |
| --- | --- | --- |
| `leos` | Bazzite standard | AMD et Intel |
| `leos-nvidia` | Bazzite NVIDIA | NVIDIA Maxwell, Pascal et Volta |
| `leos-nvidia-open` | Bazzite NVIDIA open | NVIDIA Turing et générations plus récentes |

Il s’agit de variantes matérielles d’un même système, pas d’éditions fonctionnelles différentes. Le choix de la variante doit correspondre au GPU principal. Les PC portables hybrides, les GPU de générations différentes et les périphériques spécifiques devront être testés individuellement.

Pour Gaming, les repères matériels publiés par Bazzite sont notamment 8 Go de RAM, un processeur quadricœur à 2 GHz, un GPU compatible Vulkan 1.3 ou supérieur et 50 Go libres sur SSD interne (120 Go recommandés). Ces valeurs sont des références pour l’usage Gaming, pas une promesse de performances ni une certification LEOS. Desktop peut rester utilisable sur une machine qui ne répond pas à ces repères.

Voir [la politique de compatibilité matérielle](docs/hardware-compatibility.md) et le [guide d’installation](docs/installation.md).

## Architecture technique

| Élément | Technologie |
| --- | --- |
| Système de base | Bazzite KDE Desktop |
| Construction de l’image | BlueBuild |
| Interface Gaming | Qt 6, QML et PySide6 |
| Interface Desktop | KDE Plasma |
| Préférences partagées | Modules Python LEOS et stockage utilisateur XDG |
| Manettes | Linux evdev / `python3-evdev` |
| Applications supplémentaires | Flatpak / Flathub |
| Automatisation | GitHub Actions |

LEOS réutilise les services natifs de Bazzite, KDE et Linux : gestion des sessions, réseau, Bluetooth, audio, énergie, notifications, Flatpak et mises à jour. Le projet évite de créer des services concurrents lorsqu’une interface système existe déjà.

## Validation et état du projet

Le dépôt comprend des tests unitaires Python, des contrôles d’intégration des interfaces QML et des vérifications des recettes de construction.

Les workflows [Python checks](.github/workflows/python-checks.yml) et [BlueBuild recipe checks](.github/workflows/recipe-checks.yml) vérifient notamment :

- la compilation des sources Python ;
- l’exécution de la suite de tests ;
- le lint des fichiers QML avec Qt 6 ;
- les ressources graphiques, SVG et vidéos ;
- les recettes BlueBuild et la génération des Containerfiles.

Un workflow de construction manuelle de l’image existe également. Il exécute les tests et contrôles préalables, vérifie la paire de clés Cosign, puis prévoit la publication des trois variantes dans GitHub Container Registry.

**Ces contrôles ne sont pas des essais sur un ordinateur physique.** Ils ne valident pas encore l’installation, le rendu exact de KDE, le comportement des pilotes, les transitions de session, la lecture vidéo sur le matériel cible ou les performances des jeux.

### État des livrables

| Livrable | État |
| --- | --- |
| Sources des applications LEOS | Présentes dans le dépôt |
| Thème partagé à deux couleurs A/B | Implémenté dans le code |
| Bibliothèque Gaming et intégrations documentées | Implémentées en partie, selon les sources et formats |
| Service de tri des téléchargements | Présent et référencé au démarrage de session KDE |
| Tests Python et lint QML | Automatisés par GitHub Actions |
| Recettes BlueBuild standard et NVIDIA | Présentes ; validation automatisée disponible |
| Images LEOS publiées et signées | Trois variantes disponibles dans GHCR (tag e33a010-45) |
| ISO installateur standard (ancienne chaîne) | Générée et signée ; validation physique non concluante |
| Nouvelle chaîne Titanoboa Live | Candidate sur une branche dédiée ; construction et tests VM à effectuer |
| ISO NVIDIA legacy / moderne | À générer |
| Validation sur plusieurs PC physiques | À effectuer |
| Validation sur plusieurs PC physiques | À effectuer |

## Construction de l’image et de l’ISO

La construction est volontairement séparée de la génération de l’ISO.

### 1. Préparer la signature

Le workflow de construction exige deux éléments correspondants :

- le fichier public `cosign.pub` à la racine du dépôt ;
- le secret GitHub `SIGNING_SECRET`, contenant la clé privée associée.

Le workflow vérifie que les deux clés correspondent avant d’autoriser la publication. Ne place jamais la clé privée dans le dépôt.

### 2. Construire et publier l’image

Le workflow GitHub Actions **Build LEOS** est déclenché manuellement. Il lance les contrôles préalables, puis construit les variantes standard, NVIDIA legacy et NVIDIA open. Les images publiées sont destinées à GitHub Container Registry.

### 3. Générer l’ISO

Le workflow historique **Generate LEOS installer ISO** utilise encore l’ancien générateur BlueBuild et reste uniquement pour comparaison. La branche `feature/titanoboa-installer` ajoute le workflow **Generate LEOS Titanoboa Live installer ISO**. Après avoir reconstruit les trois images LEOS sur cette branche (elles incluent une nouvelle politique de signatures), ce workflow candidat permet de choisir :

- la variante matérielle ;
- le tag de l’image publiée.

Le workflow Titanoboa vérifie la signature Cosign, embarque l’image LEOS dans un environnement Live KDE basé sur Bazzite, génère l’ISO et produit un fichier de somme SHA-256 ainsi qu’un manifeste signé. Cette chaîne reste expérimentale : aucun démarrage ni aucune installation VM ne sont encore validés. Voir [la conception de l’installateur Titanoboa](docs/titanoboa-installer.md).

Les images sont déjà construites et signées, et l’ISO standard candidate a été générée puis signée par GitHub Actions (run 43946765765). Cela ne constitue pas une validation de l’installation : le contrôle de structure UEFI et les sommes cryptographiques ne remplacent pas un démarrage en machine virtuelle, une installation sur disque de test et des essais sur matériel réel.

L’ISO candidate ne doit pas être utilisée sur le seul ordinateur principal ni pour un dual boot réel tant que le diagnostic des premiers échecs n’est pas terminé. Consulte les [consignes de validation de l’ISO](docs/iso-validation.md), le [guide d’installation](docs/installation.md) et le [guide de récupération](docs/recovery.md).

## Documentation

- [Architecture générale](docs/architecture.md)
- [Premier démarrage](docs/first-run.md)
- [Sauvegardes et récupération](docs/recovery.md)
- [Compatibilité matérielle](docs/hardware-compatibility.md)
- [Matrice de validation matérielle](docs/hardware-validation.md)
- [Bluetooth](docs/bluetooth.md)
- [Construction et signature](docs/build.md)
- [Validation de l’ISO et du support USB](docs/iso-validation.md)
- [Packaging](docs/packaging.md)
- [Installation](docs/installation.md)
- [Architecture de l’installateur Titanoboa](docs/titanoboa-installer.md)

## Structure du dépôt

```text
LEOS/
├── .github/scripts/     # Vérification des images, signatures et ISO
├── .github/workflows/   # Tests, validation, construction, ISO et site
├── aurorae/             # Décorations de fenêtres KDE
├── branding/            # Emblèmes, fonds d’écran, vidéos et sons
├── components/          # Composants partagés de l’interface
├── control_center/      # Centre de contrôle LEOS
├── controller_center/   # Centre des manettes
├── desktop/             # Thèmes, menu, notifications et intégration KDE
├── docs/                # Architecture, compatibilité, installation et guides
├── files/leos-config/   # Configuration système déployée dans l’image
├── gaming/              # Interface Gaming et bibliothèque
├── icons/               # Icônes LEOS
├── installer/           # Image Live et hooks Anaconda/Titanoboa
├── launcher/            # Sélecteur de modes et transitions
├── leos_core/           # Préférences et fonctions communes
├── packaging/           # Intégration et métadonnées de paquetage
├── plasma-theme/        # Thème Plasma LEOS
├── recipes/             # Recettes BlueBuild
├── shop/                # Catalogue et gestion Flatpak
├── tests/               # Tests Python et contrats d’intégration
└── website/             # Site officiel et centre de téléchargement
```

---

**LEOS — One system. Two experiences.**


## Site officiel

Le site vitrine et le centre de téléchargement sont préparés dans [`website/`](website/README.md). Une ISO candidate existe, mais aucun téléchargement public n’est ouvert tant que le démarrage, l’installation et la compatibilité matérielle ne sont pas validés.
