# Construire et vérifier LEOS

## État

La recette BlueBuild `recipes/recipe.yml` décrit une image basée sur Bazzite KDE Desktop. Les contrôles automatisés GitHub Actions ont réussi : compilation des sources Python, lint Qt 6 de toutes les interfaces QML, validation des vidéos (flux audio/vidéo et décodage complet), vérification SHA-256 des huit ressources déployées, validation BlueBuild et génération du Containerfile. Le workflow de construction/publication reste manuel (`workflow_dispatch`) ; aucune image LEOS n'a encore été compilée. Il ne doit pas être déclenché avant d'avoir vérifié la clé de signature et préparé un environnement de test.

## Base retenue

La recette utilise `ghcr.io/ublue-os/bazzite:stable`, c'est-à-dire la variante Desktop KDE de Bazzite. Elle correspond à notre choix : KDE reste le bureau, tandis que Gaming Mode est une application LEOS plein écran au-dessus de KDE. Nous ne sélectionnons pas l'image `bazzite-deck`, qui apporte sa propre session Steam Gaming Mode. La documentation Bazzite distingue bien les images Desktop sans Steam Gaming Mode des images Deck conçues pour démarrer dans cette session.

La variante Bazzite standard vise les GPU AMD/Intel ; les images NVIDIA sont séparées en variantes dédiées. LEOS dispose maintenant de trois recettes partageant les mêmes modules : standard AMD/Intel, NVIDIA legacy et NVIDIA open pour les générations récentes. Leur construction et leur validation sur GPU réels restent obligatoires avant toute certification.

## Contenu prévu de l'image

Le Centre de contrôle possède des pages Apparence, Matériel & connexions, Performances et Paramètres KDE. Les raccourcis matériels sont limités à une liste de modules KDE connue ; `kcmshell6` est préféré et `systemsettings` sert de solution de repli. La disponibilité de chaque KCM doit être confirmée dans l'image réelle avec `kcmshell6 --list`.

La recette ajoute les paquets Fedora `python3-pyside6`, `python3-psutil`, `python3-evdev` et `qt6-qtmultimedia`. Le tableau de bord du Centre de contrôle réutilise le moniteur système du Gaming Mode : CPU, mémoire, température CPU si le capteur est exposé, occupation du système de fichiers `/` et débits réseau agrégés ; les valeurs inconnues restent indiquées comme indisponibles. Le sélecteur de modes affiche un guide de premier démarrage non bloquant, puis mémorise sa lecture dans les préférences utilisateur. Après la sélection de Desktop Mode, le lanceur peut démarrer `leos-default-apps-setup`, qui propose Brave (`com.brave.Browser`), LibreOffice (`org.libreoffice.LibreOffice`) et VLC (`org.videolan.VLC`) comme applications facultatives. Le script exige une confirmation KDE explicite avant d'ajouter Flathub ou d'installer quoi que ce soit ; le refus est mémorisé et aucun logiciel n'est installé en session sans interface graphique. Le script n'est pas lancé en arrière-plan à l'ouverture de session ni pendant Gaming Mode. Si une installation échoue, le script poursuit les autres applications, ne marque pas le parcours comme terminé et pourra retenter les applications manquantes lors d'une prochaine sélection de Desktop ; les applications déjà présentes sont ignorées. La recette copie ensuite les dossiers Gaming, launcher, Control Center, Controller Center, boutique, core et branding dans `/usr/share/leos`. Elle installe les entrées KDE du sélecteur de modes, du Centre de contrôle, du Centre des manettes et de la boutique, ainsi que l'autostart de session. Qt Multimedia fournit le moteur des introductions vidéo : Desktop utilise `desktop-intro.mov`, Gaming utilise `gaming-intro.mp4` et `gaming-roar-reference.mp4` reste une référence non jouée automatiquement. Le sélecteur et Gaming lancent les introductions lors des transitions, avec son intégré configurable indépendamment et repli sur erreur/délai. Les six ressources visuelles sont présentes dans le dépôt ; les contrôles CI vérifient désormais la présence de flux vidéo et audio dans les trois vidéos. La lecture effective et la synchronisation doivent encore être validées sur une session Bazzite réelle. Les noms de paquets sont publiés dans Fedora ; leur présence et leur compatibilité doivent tout de même être confirmées avec la version exacte de Bazzite utilisée pour le build.

## Bluetooth

Le Bluetooth est un prérequis fonctionnel pour LEOS, dans les deux modes. La stratégie retenue est de conserver la pile BlueZ, l'intégration KDE et PipeWire fournies par la base Bazzite lorsque présentes. La première image de test devra confirmer la présence et le démarrage de `bluetooth.service`, la disponibilité des paramètres KDE et le fonctionnement des périphériques audio et manettes. Aucun ajout de paquet ou override BlueZ ne doit être introduit sans preuve d'un composant manquant : des régressions BlueZ/KDE ont déjà été signalées en amont, ce qui renforce la nécessité de tester les versions réellement embarquées plutôt que de figer arbitrairement une version. Voir [la checklist Bluetooth](bluetooth.md).

## Signature de l'image

BlueBuild attend la clé privée cosign dans le secret GitHub `SIGNING_SECRET`. La clé privée ne doit jamais être commitée dans le dépôt.

Préparation à effectuer depuis un poste de confiance disposant de cosign, dans un clone local du dépôt :

1. À la racine du dépôt, générer la paire :
   ```bash
   umask 077
   cosign generate-key-pair
   ```
   Cosign crée `cosign.key` et `cosign.pub`. Lorsque Cosign demande un mot de passe, laisser le champ vide et appuyer deux fois sur Entrée : BlueBuild précise que la clé destinée à son workflow GitHub Actions ne doit pas être chiffrée par une phrase secrète.
2. Vérifier que les deux fichiers existent, puis enregistrer le contenu de `cosign.key` dans le secret Actions nommé exactement `SIGNING_SECRET` :
   ```bash
   test -s cosign.key && test -s cosign.pub
   gh secret set SIGNING_SECRET < cosign.key
   ```
   Sans GitHub CLI, ouvrir **Settings → Secrets and variables → Actions → New repository secret** et coller le contenu de `cosign.key` dans la valeur du secret.
3. Ajouter uniquement la clé publique à la racine du dépôt :
   ```bash
   git add cosign.pub
   git commit -m "chore(signing): add LEOS verification key"
   ```
4. Garder la clé privée `cosign.key` hors du dépôt, avec des permissions locales restrictives, et en conserver une sauvegarde dans un coffre sécurisé. Ne jamais la coller dans une conversation, une issue, un ticket ou un journal CI.

Le workflow LEOS vérifie ensuite cryptographiquement que le secret et `cosign.pub` forment bien une paire avant d'autoriser la publication. Ne jamais afficher le secret pour tenter de le vérifier manuellement.

Le module BlueBuild `signing` est présent dans la recette afin de configurer les règles de vérification de l'image. Avant la compilation, le workflow installe Cosign, signe un petit fichier temporaire avec la clé privée fournie par le secret, puis vérifie cette signature avec `cosign.pub`. Cette vérification confirme que les deux clés forment bien une paire. Le fichier privé temporaire est limité aux permissions utilisateur et supprimé à la fin de l'étape ; la clé privée n'est jamais écrite dans le dépôt ni affichée volontairement dans les logs.

## Avant la première compilation

- Vérifier le contenu du workflow `.github/workflows/build.yml`, notamment le contrôle cryptographique de correspondance entre la clé privée et `cosign.pub`.
- [x] Valider `recipes/recipe.yml` avec le CLI BlueBuild (`bluebuild validate`) et générer un Containerfile (`bluebuild generate`) dans le workflow GitHub Actions.
- Vérifier la présence des trois logos, des trois vidéos et des deux fonds d'écran 4K aux chemins indiqués dans `branding/ASSET_MANIFEST.md`. Le workflow de validation contrôle la présence des flux vidéo/audio et décode intégralement les trois vidéos avec FFmpeg ; les SHA-256 de `branding/SHA256SUMS` identifient les originaux transmis dans la conversation et ne certifient pas les copies vidéo actuellement hébergées.
- Confirmer que le secret `SIGNING_SECRET` est configuré et que la clé publique correspondante est disponible.
- Déclencher le workflow manuellement seulement après ces contrôles.

La documentation BlueBuild recommande de valider/générer la recette avec son CLI avant de construire l'image. La compilation et surtout le premier démarrage doivent ensuite être testés sur une machine de test, jamais directement sur le seul poste de travail principal.

Références techniques : [format de recette BlueBuild](https://blue-build.org/reference/recipe/), [module systemd](https://blue-build.org/reference/modules/systemd/), [module copy](https://blue-build.org/reference/modules/copy/), [module DNF](https://blue-build.org/reference/modules/dnf/) et [FAQ Bazzite sur les variantes Desktop/Deck](https://docs.bazzite.gg/General/FAQ/).

## Prérequis encore bloquants

- Le dépôt ne contient pas encore le fichier public `cosign.pub`. Il faudra ajouter la clé publique correspondant au secret Actions `SIGNING_SECRET`.
- L'existence et la validité du secret privé `SIGNING_SECRET` ne sont pas vérifiables depuis les fichiers du dépôt. La clé privée doit être créée et conservée sur un poste de confiance ; ne jamais la transmettre dans une conversation ni la committer.
- Les logos officiels, les trois vidéos d'introduction/référence et les deux fonds d'écran 4K sont présents dans `branding/`. Le rendu des fonds SVG et JPEG liés, la restitution vidéo/audio et les transitions doivent encore être validés sur une session Bazzite réelle.
- Une image de test devra être démarrée sur une machine de test Bazzite pour confirmer les paquets RPM, les modules QML, le Bluetooth, les manettes et les transitions. Les contrôles Python et la génération du Containerfile ne remplacent pas cette validation matérielle.

Le workflow `.github/workflows/build.yml` est manuel : aucun build ni publication ne doit être déclenché tant que la signature, les ressources officielles et la machine de test ne sont pas prêts. Avant l'étape de signature, il vérifie la présence des six ressources d'origine (trois emblèmes et trois vidéos) et des deux fonds SVG, puis contrôle les huit empreintes réellement déployées via `branding/DEPLOYED_SHA256SUMS`. Le workflow de validation de recette vérifie séparément que chaque vidéo contient un flux vidéo et un flux audio décodables. Le build vérifie ensuite le secret `SIGNING_SECRET` et le fichier `cosign.pub` avant d'appeler BlueBuild.

## Validation sur matériel réel

La checklist détaillée du premier démarrage, des transitions, du Bluetooth, des manettes, du Centre de contrôle, de la boutique et du rollback est disponible dans [la checklist de validation matérielle](hardware-validation.md). Elle doit être exécutée sur un PC de test avant de considérer l'image comme prête.

## Construction ISO

Le workflow manuel `.github/workflows/iso.yml` prépare cette étape à partir d'une image LEOS déjà publiée dans GHCR. Il demande explicitement la variante matérielle (standard, NVIDIA legacy ou NVIDIA moderne) et le tag de l'image, valide le format du tag puis s'authentifie au registre. Avant toute vérification de signature, il tire l'image avec Podman et résout son empreinte SHA-256 ; les étapes Cosign et BlueBuild utilisent ensuite toutes deux cette référence immuable `ghcr.io/...@sha256:...`, jamais le tag mutable. Cela évite qu'un tag déplacé entre la vérification et la génération fasse produire une ISO à partir d'une image différente de celle qui a été vérifiée.

Après la génération, le workflow signe l'ISO et le manifeste JSON de provenance avec la clé privée du secret Actions `SIGNING_SECRET`. Le script `.github/scripts/sign-iso-artifacts.sh` utilise une copie temporaire de la clé, limitée aux permissions `0600`, vérifie immédiatement les deux signatures avec `cosign.pub`, puis supprime son répertoire temporaire. Les fichiers `.sig` de l'ISO et du manifeste sont ajoutés aux artefacts avec l'ISO, sa somme SHA-256 et le manifeste. Les artefacts GitHub Actions sont conservés pendant 14 jours. Le manifeste consigne la référence immuable de l'image source, la variante, le tag demandé, le commit, l'exécution GitHub Actions et l'empreinte SHA-256 de l'ISO ; sa propre signature protège ces informations contre une modification après génération.

Après téléchargement, vérifier les fichiers depuis le dossier qui contient l'ISO, le manifeste, les deux signatures et le fichier SHA-256. Pour l'exemple de la variante standard avec le tag `latest` :

```bash
sha256sum --check LEOS-standard-latest.iso.sha256
cosign verify-blob --key cosign.pub --signature LEOS-standard-latest.iso.sig LEOS-standard-latest.iso
cosign verify-blob --key cosign.pub --signature LEOS-standard-latest.iso.json.sig LEOS-standard-latest.iso.json
```

La somme SHA-256 contrôle l'intégrité du fichier ; la vérification Cosign établit que l'ISO et le manifeste ont été signés par la clé privée correspondant à la clé publique publiée dans le dépôt. Le secret `SIGNING_SECRET` doit donc être configuré pour le workflow ISO également. Ce workflow ne publie pas automatiquement une ISO et ne doit être lancé qu'après la réussite du build signé correspondant.

Cette méthode suit la documentation BlueBuild : générer l'ISO à partir de l'image publiée est le flux recommandé lorsque les images sont construites et publiées dans le cloud. L'ISO générée doit encore être testée en machine virtuelle UEFI puis sur matériel physique avant toute diffusion publique. Voir [le guide d'installation](installation.md) et [la procédure BlueBuild de génération ISO](https://blue-build.org/how-to/generate-iso/).
