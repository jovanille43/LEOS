# Construire et vérifier LEOS

## État

Au 27 novembre 2026, `main` est au commit `dc1faf7` (fusion de la PR #73). Les contrôles Python et BlueBuild de ce commit ont réussi ; la reconstruction des trois variantes conteneur est encore en cours à la date de cet état. Le dernier lot entièrement construit et signé est basé sur `dcd8966` : run Build [#45853796496](https://github.com/jovanille43/LEOS/actions/runs/45853796496), suivi du run ISO [#45855325068](https://github.com/jovanille43/LEOS/actions/runs/45855325068). Ce dernier a généré les trois ISO (standard, NVIDIA legacy et NVIDIA open), avec checksum, digest source, manifeste de provenance et smoke test UEFI/QEMU jusqu'à l'accueil Anaconda WebUI. Le smoke test ne réalise pas d'installation sur disque. Les ISO issues de `dc1faf7` devront être produites après la fin du build courant, puis l'une d'elles devra être installée complètement en VM avant validation de livraison.

## Base retenue

La recette utilise `ghcr.io/ublue-os/bazzite:stable`, c'est-à-dire la variante Desktop KDE de Bazzite. Elle correspond à notre choix : KDE reste le bureau, tandis que Gaming Mode est une application LEOS plein écran au-dessus de KDE. Nous ne sélectionnons pas l'image `bazzite-deck`, qui apporte sa propre session Steam Gaming Mode. La documentation Bazzite distingue bien les images Desktop sans Steam Gaming Mode des images Deck conçues pour démarrer dans cette session.

La variante Bazzite standard vise les GPU AMD/Intel ; les images NVIDIA sont séparées en variantes dédiées. Les trois variantes partageant les mêmes modules — standard AMD/Intel, NVIDIA legacy et NVIDIA open — ont été construites, publiées et signées. Elles doivent encore être validées sur GPU réels avant toute certification.

## Contenu prévu de l'image

Le Centre de contrôle possède des pages Apparence, Matériel & connexions, Performances et Paramètres KDE. Les raccourcis matériels sont limités à une liste de modules KDE connue ; `kcmshell6` est préféré et `systemsettings` sert de solution de repli. La disponibilité de chaque KCM doit être confirmée dans l'image réelle avec `kcmshell6 --list`.

La recette ajoute les paquets Fedora `python3-pyside6`, `python3-psutil`, `python3-evdev`, `vulkan-tools`, `libnotify`, `aurorae`, `qt6-qtmultimedia` et `qt6-qtsvg`. Le tableau de bord du Centre de contrôle réutilise le moniteur système du Gaming Mode : CPU, mémoire, température CPU si le capteur est exposé, occupation du système de fichiers `/` et débits réseau agrégés ; les valeurs inconnues restent indiquées comme indisponibles. Le sélecteur de modes affiche un guide de premier démarrage non bloquant, puis mémorise sa lecture dans les préférences utilisateur. Après la sélection de Desktop Mode, le lanceur peut démarrer `leos-default-apps-setup`, qui propose Brave (`com.brave.Browser`), LibreOffice (`org.libreoffice.LibreOffice`) et VLC (`org.videolan.VLC`) comme applications facultatives. Le script exige une confirmation KDE explicite avant d'ajouter Flathub ou d'installer quoi que ce soit ; le refus est mémorisé et aucun logiciel n'est installé en session sans interface graphique. Le script n'est pas lancé en arrière-plan à l'ouverture de session ni pendant Gaming Mode. Si une installation échoue, le script poursuit les autres applications, ne marque pas le parcours comme terminé et pourra retenter les applications manquantes lors d'une prochaine sélection de Desktop ; les applications déjà présentes sont ignorées. La recette copie les dossiers Gaming, launcher, Centre de contrôle, Centre des manettes, Boutique et core dans `/usr/share/leos`. Pour la marque, elle installe une liste blanche de huit ressources d'exécution : les quatre emblèmes PNG transparents, les deux introductions réellement jouées et les deux fonds SVG ; elle installe également le composant QML partagé des particules. Les JPEG sources restent dans le dépôt pour régénérer les PNG et sont vérifiés séparément. L'image n'embarque ni la comparaison graphique ni la vidéo secondaire `gaming-roar-reference.mp4`, qui demeurent des références documentaires. La recette installe les entrées KDE du sélecteur de modes, du Centre de contrôle, du Centre des manettes et de la boutique, ainsi que l'autostart de session. Qt Multimedia lit `desktop-intro.mov` pour Desktop et `gaming-intro.mp4` pour Gaming, avec pistes audio intégrées, son configurable séparément des animations et repli sur erreur/délai. Les contrôles CI vérifient les empreintes des huit ressources embarquées, la structure des fonds SVG et les flux vidéo/audio des deux introductions actives. La lecture effective et la synchronisation doivent encore être validées sur une session Bazzite réelle. Les noms de paquets sont publiés dans Fedora ; leur présence et leur compatibilité doivent tout de même être confirmées avec la version exacte de Bazzite utilisée pour le build.

## Bluetooth

Le Bluetooth est un prérequis fonctionnel pour LEOS, dans les deux modes. La stratégie retenue est de conserver la pile BlueZ, l'intégration KDE et PipeWire fournies par la base Bazzite lorsque présentes. La validation sur PC physique devra confirmer la présence et le démarrage de `bluetooth.service`, la disponibilité des paramètres KDE et le fonctionnement des périphériques audio et manettes. Une VM standard ne suffit pas à certifier le Bluetooth matériel. Aucun ajout de paquet ou override BlueZ ne doit être introduit sans preuve d'un composant manquant : des régressions BlueZ/KDE ont déjà été signalées en amont, ce qui renforce la nécessité de tester les versions réellement embarquées plutôt que de figer arbitrairement une version. Voir [la checklist Bluetooth](bluetooth.md).

## Signature de l'image

BlueBuild attend la clé privée cosign dans le secret GitHub `SIGNING_SECRET`. La clé privée ne doit jamais être commitée dans le dépôt.

La paire Cosign de LEOS est déjà préparée : la clé privée est chiffrée et la clé publique correspondante `cosign.pub` est versionnée à la racine du dépôt. GitHub Actions utilise deux secrets distincts :

1. `SIGNING_SECRET` contient la clé privée chiffrée.
2. `COSIGN_PASSWORD` contient sa phrase de déverrouillage.

Le contrôle manuel de correspondance des clés a réussi le 17 novembre 2026. Le workflow de build répète cette vérification hors ligne avant toute publication. Les valeurs des secrets ne sont pas consultables depuis le dépôt ; ne jamais les afficher dans les logs, les transmettre dans une conversation ou les committer.

Le module BlueBuild `signing` est présent dans la recette afin de configurer les règles de vérification de l'image. Avant la compilation, le workflow installe Cosign, signe un petit fichier temporaire avec la clé privée fournie par le secret, puis vérifie cette signature avec `cosign.pub`. Cette vérification confirme que les deux clés forment bien une paire. Le fichier privé temporaire est limité aux permissions utilisateur et supprimé à la fin de l'étape ; la clé privée n'est jamais écrite dans le dépôt ni affichée volontairement dans les logs.

## Contrôles de construction et de publication

- [x] Vérification du workflow `.github/workflows/build.yml`, y compris le précontrôle cryptographique de correspondance entre la clé fournie par le secret et `cosign.pub`.
- [x] Validation des trois recettes BlueBuild et génération des Containerfiles par GitHub Actions.
- [x] Vérification de présence des ressources officielles, décodage des flux audio/vidéo et contrôle des huit empreintes déployées.
- [x] Contrôle cryptographique de la paire Cosign et vérification des prérequis de signature par GitHub Actions. Les valeurs des secrets restent privées et ne sont pas affichées.
- [x] Publication et signature des trois images conteneur dans GHCR et génération des trois ISO depuis les images publiées (run #45855325068, commit `dcd8966`).
- [ ] Répéter le build et la génération ISO pour `dc1faf7`, qui inclut les améliorations de la PR #73.

La validation BlueBuild de la recette et la génération des Containerfiles ont réussi. Le run #45855325068 confirme le démarrage UEFI/QEMU des trois ISO jusqu'à Anaconda WebUI ; il ne confirme pas l'installation sur disque. L'étape suivante est l'installation interactive de l'ISO correspondant au commit courant dans une VM UEFI avec un disque virtuel dédié, puis les essais sur matériel physique. Ne jamais effectuer le premier essai d'installation sur le seul poste de travail principal.

Références techniques : [format de recette BlueBuild](https://blue-build.org/reference/recipe/), [module systemd](https://blue-build.org/reference/modules/systemd/), [module copy](https://blue-build.org/reference/modules/copy/), [module DNF](https://blue-build.org/reference/modules/dnf/) et [FAQ Bazzite sur les variantes Desktop/Deck](https://docs.bazzite.gg/General/FAQ/).

## État des validations restantes

- [x] Le fichier public `cosign.pub` est présent à la racine du dépôt.
- [x] La paire Cosign a passé le contrôle cryptographique GitHub Actions ; les secrets n'ont pas été exposés.
- [x] Le workflow de build vérifie la présence des deux secrets et la correspondance cryptographique avec `cosign.pub` avant publication.
- [x] Les ressources déployées sont présentes et leurs empreintes sont contrôlées. Le rendu des fonds, la restitution vidéo/audio et les transitions restent à valider en session Bazzite réelle.
- [ ] Installer l'ISO du commit `dc1faf7` dans une VM UEFI, sur un disque virtuel dédié, puis vérifier la création du compte et le premier démarrage.
- [ ] Vérifier les transitions Desktop/Gaming, le profil Plasma LEOS, les services, la vidéo et l'audio après installation et second redémarrage.
- [ ] Valider le Bluetooth, les manettes, les GPU réels, la veille et les écrans sur PC physique de test.
- [x] Générer les ISO standard, NVIDIA legacy et NVIDIA open sur `dcd8966` et les démarrer sous UEFI/QEMU jusqu'à Anaconda WebUI.
- [ ] Répéter le build et la génération ISO pour `dc1faf7` après le build d'image en cours.

Le workflow `.github/workflows/build.yml` est déclenché manuellement et automatiquement sur `main` lorsque ses chemins de sources/recettes changent. Après la réussite de **Build LEOS**, le workflow `.github/workflows/iso.yml` est déclenché automatiquement et génère séquentiellement les trois variantes (`standard`, `nvidia-legacy`, `nvidia-modern`). Pour chaque image, il vérifie le digest, la signature Cosign et le tag avant génération ; l'artefact comprend l'ISO, le SHA-256, le digest source et le manifeste de provenance.

## Validation sur matériel réel

La checklist détaillée du premier démarrage, des transitions, du Bluetooth, des manettes, du Centre de contrôle, de la boutique et du rollback est disponible dans [la checklist de validation matérielle](hardware-validation.md). Elle doit être exécutée sur un PC de test avant de considérer l'image comme prête.

## Construction ISO

Le workflow `.github/workflows/iso.yml` génère une ISO depuis une image publiée dans GHCR. Il peut être lancé manuellement avec la variante et le tag souhaités ; après un build `main` réussi, il est aussi déclenché automatiquement et construit les trois variantes une par une afin de limiter la pression sur les runners et le stockage. Pour chaque variante, il résout le digest, vérifie la signature Cosign avec la clé publique LEOS, vérifie que le tag pointe toujours vers le même digest puis génère l'ISO. L'artefact inclut l'ISO, son SHA-256, le digest de l'image et le manifeste de provenance, conservés 14 jours. Le run #45855325068 a généré les trois ISO sur le commit `dcd8966` ; la répétition sur le commit `dc1faf7` est en attente de la fin du build des images.

**Correction du chemin d'installation :** l'exécution du run 44257827294 utilisait `WEB_UI=false`, donc l'interface Anaconda GTK historique. Fedora 45 a basculé les médias Atomic Desktop vers Anaconda WebUI. Le workflow LEOS active maintenant explicitement l'option BlueBuild `--web-ui`, disponible dans la CLI v0.9.42, afin d'inclure `anaconda-webui` dans le média généré. C'est un alignement avec le chemin Fedora 45 ; ce changement n'établit pas encore la cause racine de l'échec observé sur matériel et doit être validé avec une nouvelle ISO.

Cette méthode suit la documentation BlueBuild pour la génération à partir d'une image publiée. Toute nouvelle ISO doit encore être testée en machine virtuelle UEFI avec un disque virtuel dédié, puis sur matériel physique de test avant toute diffusion publique. Voir [le guide d'installation](installation.md) et [la procédure BlueBuild de génération ISO](https://blue-build.org/how-to/generate-iso/).
