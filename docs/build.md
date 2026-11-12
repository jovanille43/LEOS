# Construire et vérifier LEOS

## État

La recette BlueBuild `recipes/recipe.yml` décrit une image basée sur Bazzite KDE Desktop. Les contrôles automatisés GitHub Actions ont réussi : validation BlueBuild, génération du Containerfile, syntaxe du script de premier démarrage et tests Python. Le workflow de construction/publication reste manuel (`workflow_dispatch`) ; aucune image LEOS n'a encore été compilée. Il ne doit pas être déclenché avant d'avoir vérifié la clé de signature et préparé un environnement de test.

## Base retenue

La recette utilise `ghcr.io/ublue-os/bazzite:stable`, c'est-à-dire la variante Desktop KDE de Bazzite. Elle correspond à notre choix : KDE reste le bureau, tandis que Gaming Mode est une application LEOS plein écran au-dessus de KDE. Nous ne sélectionnons pas l'image `bazzite-deck`, qui apporte sa propre session Steam Gaming Mode. La documentation Bazzite distingue bien les images Desktop sans Steam Gaming Mode des images Deck conçues pour démarrer dans cette session.

La variante Bazzite standard vise les GPU AMD/Intel ; les images NVIDIA sont séparées en variantes dédiées. Une variante NVIDIA LEOS devra donc être préparée et validée séparément avant de prétendre à une compatibilité NVIDIA complète.

## Contenu prévu de l'image

Le Centre de contrôle possède des pages Apparence, Matériel & connexions, Performances et Paramètres KDE. Les raccourcis matériels sont limités à une liste de modules KDE connue ; `kcmshell6` est préféré et `systemsettings` sert de solution de repli. La disponibilité de chaque KCM doit être confirmée dans l'image réelle avec `kcmshell6 --list`.

La recette ajoute les paquets Fedora `python3-pyside6`, `python3-psutil`, `python3-evdev` et `qt6-qtmultimedia`. Le tableau de bord du Centre de contrôle réutilise le moniteur système du Gaming Mode : CPU, mémoire, température CPU si le capteur est exposé, occupation du système de fichiers `/` et débits réseau agrégés ; les valeurs inconnues restent indiquées comme indisponibles. Un service systemd utilisateur, activé globalement via le module BlueBuild `systemd`, installe une seule fois Brave (`com.brave.Browser`), LibreOffice (`org.libreoffice.LibreOffice`) et VLC (`org.videolan.VLC`) dans le profil utilisateur. Un marqueur persistant empêche leur réinstallation après une désinstallation volontaire ; les trois applications restent donc librement désinstallables depuis la boutique LEOS. La recette copie ensuite les dossiers Gaming, launcher, Control Center, Controller Center, boutique, core et branding dans `/usr/share/leos`. Elle installe les entrées KDE du sélecteur de modes, du Centre de contrôle, du Centre des manettes et de la boutique, ainsi que l'autostart de session. Qt Multimedia fournit le moteur des introductions vidéo : Desktop utilise `desktop-intro.mov`, Gaming utilise `gaming-intro.mp4` et `gaming-roar-reference.mp4` reste une référence non jouée automatiquement. Le sélecteur et Gaming lancent les introductions lors des transitions, avec son intégré configurable indépendamment et repli sur erreur/délai. Les six ressources visuelles sont présentes dans le dépôt ; les contrôles CI vérifient désormais la présence de flux vidéo et audio dans les trois vidéos. La lecture effective et la synchronisation doivent encore être validées sur une session Bazzite réelle. Les noms de paquets sont publiés dans Fedora ; leur présence et leur compatibilité doivent tout de même être confirmées avec la version exacte de Bazzite utilisée pour le build.

## Bluetooth

Le Bluetooth est un prérequis fonctionnel pour LEOS, dans les deux modes. La stratégie retenue est de conserver la pile BlueZ, l'intégration KDE et PipeWire fournies par la base Bazzite lorsque présentes. La première image de test devra confirmer la présence et le démarrage de `bluetooth.service`, la disponibilité des paramètres KDE et le fonctionnement des périphériques audio et manettes. Aucun ajout de paquet ou override BlueZ ne doit être introduit sans preuve d'un composant manquant : des régressions BlueZ/KDE ont déjà été signalées en amont, ce qui renforce la nécessité de tester les versions réellement embarquées plutôt que de figer arbitrairement une version. Voir [la checklist Bluetooth](bluetooth.md).

## Signature de l'image

BlueBuild attend la clé privée cosign dans le secret GitHub `SIGNING_SECRET`. La clé privée ne doit jamais être commitée dans le dépôt.

Préparation à effectuer depuis un poste de confiance disposant de cosign :

1. Générer une paire de clés cosign sans phrase secrète, selon la procédure officielle BlueBuild.
2. Copier le contenu de `cosign.key` dans le secret Actions `SIGNING_SECRET` du dépôt GitHub.
3. Ajouter uniquement `cosign.pub` à la racine du dépôt.
4. Conserver la clé privée hors du dépôt et en lieu sûr.

Le module BlueBuild `signing` est présent dans la recette afin de configurer les règles de vérification de l'image.

## Avant la première compilation

- Vérifier le contenu du workflow `.github/workflows/build.yml`.
- [x] Valider `recipes/recipe.yml` avec le CLI BlueBuild (`bluebuild validate`) et générer un Containerfile (`bluebuild generate`) dans le workflow GitHub Actions.
- Vérifier la présence des trois logos et des trois vidéos aux chemins indiqués dans `branding/ASSET_MANIFEST.md`. Le workflow de validation contrôle la présence des flux vidéo/audio ; les SHA-256 de `branding/SHA256SUMS` identifient les originaux transmis dans la conversation et ne certifient pas les copies vidéo actuellement hébergées.
- Confirmer que le secret `SIGNING_SECRET` est configuré et que la clé publique correspondante est disponible.
- Déclencher le workflow manuellement seulement après ces contrôles.

La documentation BlueBuild recommande de valider/générer la recette avec son CLI avant de construire l'image. La compilation et surtout le premier démarrage doivent ensuite être testés sur une machine de test, jamais directement sur le seul poste de travail principal.

Références techniques : [format de recette BlueBuild](https://blue-build.org/reference/recipe/), [module systemd](https://blue-build.org/reference/modules/systemd/), [module copy](https://blue-build.org/reference/modules/copy/), [module DNF](https://blue-build.org/reference/modules/dnf/) et [FAQ Bazzite sur les variantes Desktop/Deck](https://docs.bazzite.gg/General/FAQ/).

## Prérequis encore bloquants

- Le dépôt ne contient pas encore le fichier public `cosign.pub`. Il faudra ajouter la clé publique correspondant au secret Actions `SIGNING_SECRET`.
- L'existence et la validité du secret privé `SIGNING_SECRET` ne sont pas vérifiables depuis les fichiers du dépôt. La clé privée doit être créée et conservée sur un poste de confiance ; ne jamais la transmettre dans une conversation ni la committer.
- Les logos officiels et les trois vidéos d'introduction/référence sont présents dans `branding/`. Les fonds d'écran restent à intégrer ; le rendu vidéo/audio et les transitions doivent encore être validés sur une session Bazzite réelle.
- Une image de test devra être démarrée sur une machine de test Bazzite pour confirmer les paquets RPM, les modules QML, le Bluetooth, les manettes et les transitions. Les contrôles Python et la génération du Containerfile ne remplacent pas cette validation matérielle.

Le workflow `.github/workflows/build.yml` est manuel : aucun build ni publication ne doit être déclenché tant que la signature, les ressources officielles et la machine de test ne sont pas prêts. Avant l'étape de signature, il vérifie la présence des six fichiers officiels ; le workflow de validation de recette vérifie séparément que chaque vidéo contient un flux vidéo et un flux audio lisibles par ffprobe. Il vérifie ensuite le secret `SIGNING_SECRET` et le fichier `cosign.pub` avant d'appeler BlueBuild.

## Validation sur matériel réel

La checklist détaillée du premier démarrage, des transitions, du Bluetooth, des manettes, du Centre de contrôle, de la boutique et du rollback est disponible dans [la checklist de validation matérielle](hardware-validation.md). Elle doit être exécutée sur un PC de test avant de considérer l'image comme prête.

## Construction ISO

L'ISO installable est une étape ultérieure. La priorité est d'abord de produire une image bootable signée, de la tester et de vérifier les mises à jour/rollback. La procédure ISO sera choisie après validation de l'image de base, en suivant le processus BlueBuild pour les images Fedora Atomic.
