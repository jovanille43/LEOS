# Journal des modifications LEOS

Les entrées sont regroupées par version. Tant qu'aucune release qualifiée n'existe, les modifications restent dans `[Unreleased]`.

## [Unreleased]

### Ajouté
- Import de jeux depuis un dossier choisi pour Dolphin (GameCube/Wii), PCSX2 (PS2) et PPSSPP (PSP), avec parcours borné, chemins revalidés et accès Flatpak en lecture seule.
- Détection plus robuste des manettes Linux via les interfaces joydev/evdev, avec tests contre les faux positifs clavier/tactile.
- Gaming plus accessible : textes agrandis, noms et rôles Qt accessibles, états vides actionnables, contraste de focus et aide clavier/manette.
- Protection contre les demandes concurrentes d'application du dock Plasma.
- Trois variantes d'images conteneur LEOS : standard AMD/Intel, NVIDIA legacy et NVIDIA open.
- Publication et signature Cosign des trois images dans GHCR.
- Workflow manuel de génération d'ISO avec vérification de la signature et du digest source.
- Première ISO installateur standard générée avec succès.
- Guides de validation de l'ISO en VM et de validation matérielle physique.

### À valider avant la première release
- Valider les transitions Desktop/Gaming, le guide de premier démarrage, le réseau, l'audio et les redémarrages répétés dans la VM (l'installation standard et l'accès au premier bureau KDE sont déjà confirmés).
- Fonctions Desktop/Gaming, média, audio, réseau et stabilité après installation.
- Validation physique des variantes matérielles qui seront annoncées comme prises en charge.
- Publication versionnée avec ISO, SHA-256, digest source et notes de version.

Aucune version stable ou tag de release n'est encore publié.
