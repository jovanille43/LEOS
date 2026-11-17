# Construire et vérifier LEOS

## État

La recette BlueBuild `recipes/recipe.yml` décrit une image basée sur Bazzite KDE Desktop. Le workflow de construction/publication a réussi sur la branche `feature/custom-two-color-themes` le 16 novembre 2026 (run 43933044510, commit e33a010). Les tests Python, le lint Qt 6/QML, la validation des ressources de marque, les contrôles Cosign et les trois publications standard AMD/Intel, NVIDIA legacy et NVIDIA open ont réussi. Les trois images sont publiées et signées dans GHCR avec le tag e33a010-45. Une ISO installateur standard a ensuite été générée et signée (run 43946765765). Sa validation physique n’a pas abouti : échec du contrôle média puis échec Anaconda à l’étape d’installation des logiciels. La cause n’est pas connue ; l’intégrité du fichier téléchargé et de la clé USB doit d’abord être vérifiée. Aucune installation réussie ni compatibilité matérielle n’est encore certifiée.

## Base retenue

La recette utilise `ghcr.io/ublue-os/bazzite:stable`, c'est-à-dire la variante Desktop KDE de Bazzite. Elle correspond à notre choix : KDE reste le bureau, tandis que Gaming Mode est une application LEOS plein écran au-dessus de KDE. Nous ne sélectionnons pas l'image `bazzite-deck`, qui apporte sa propre session Steam Gaming Mode. La documentation Bazzite distingue bien les images Desktop sans Steam Gaming Mode des images Deck conçues pour démarrer dans cette session.

La variante Bazzite standard vise les GPU AMD/Intel ; les images NVIDIA sont séparées en variantes dédiées. LEOS dispose maintenant de trois recettes partageant les mêmes modules : standard AMD/Intel, NVIDIA legacy et NVIDIA open pour les générations récentes. Leur construction et leur validation sur GPU réels restent obligatoires avant toute certification.

## Contenu prévu de l'image

Le Centre de contrôle possède des pages Apparence, Matériel & connexions, Performances et Paramètres KDE. Les raccourcis matériels sont limités à une liste de modules KDE connue ; `kcmshell6` est préféré et `systemsettings` sert de solution de repli. La disponibilité de chaque KCM doit être confirmée dans l'image réelle avec `kcmshell6 --list`.

La recette ajoute les paquets Fedora `python3-pyside6`, `python3-psutil`, `python3-evdev` et `qt6-qtmultimedia`. Le tableau de bord du Centre de contrôle réutilise le moniteur système du Gaming Mode : CPU, mémoire, température CPU si le capteur est exposé, occupation du système de fichiers `/` et débits réseau agrégés ; les valeurs inconnues restent indiquées comme indisponibles. Le sélecteur de modes affiche un guide de premier démarrage non bloquant, puis mémorise sa lecture dans les préférences utilisateur. Après la sélection de Desktop Mode, le lanceur peut démarrer `leos-default-apps-setup`, qui propose Brave (`com.brave.Browser`), LibreOffice (`org.libreoffice.LibreOffice`) et VLC (`org.videolan.VLC`) comme applications facultatives. Le script exige une confirmation KDE explicite avant d'ajouter Flathub ou d'installer quoi que ce soit ; le refus est mémorisé et aucun logiciel n'est installé en session sans interface graphique. Le script n'est pas lancé en arrière-plan à l'ouverture de session ni pendant Gaming Mode. Si une installation échoue, le script poursuit les autres applications, ne marque pas le parcours comme terminé et pourra retenter les applications manquantes lors d'une prochaine sélection de Desktop ; les applications déjà présentes sont ignorées. La recette copie ensuite les dossiers Gaming, launcher, Control Center, Controller Center, boutique, core et branding dans `/usr/share/leos`. Elle installe les entrées KDE du sélecteur de modes, du Centre de contrôle, du Centre des manettes et de la boutique, ainsi que l'autostart de session. Qt Multimedia fournit le moteur des introductions vidéo : Desktop utilise `desktop-intro.mov`, Gaming utilise `gaming-intro.mp4` et `gaming-roar-reference.mp4` reste une référence non jouée automatiquement. Le sélecteur et Gaming lancent les introductions lors des transitions, avec son intégré configurable indépendamment et repli sur erreur/délai. Les six ressources visuelles sont présentes dans le dépôt ; les contrôles CI vérifient désormais la présence de flux vidéo et audio dans les trois vidéos. La lecture effective et la synchronisation doivent encore être validées sur une session Bazzite réelle. Les noms de paquets sont publiés dans Fedora ; leur présence et leur compatibilité doivent tout de même être confirmées avec la version exacte de Bazzite utilisée pour le build.

## Bluetooth

Le Bluetooth est un prérequis fonctionnel pour LEOS, dans les deux modes. La stratégie retenue est de conserver la pile BlueZ, l'intégration KDE et PipeWire fournies par la base Bazzite lorsque présentes. La première validation sur une machine de test devra confirmer la présence et le démarrage de `bluetooth.service`, la disponibilité des paramètres KDE et le fonctionnement des périphériques audio et manettes. Aucun ajout de paquet ou override BlueZ ne doit être introduit sans preuve d'un composant manquant : des régressions BlueZ/KDE ont déjà été signalées en amont, ce qui renforce la nécessité de tester les versions réellement embarquées plutôt que de figer arbitrairement une version. Voir [la checklist Bluetooth](bluetooth.md).

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

## Avant toute nouvelle compilation

- Vérifier le contenu du workflow `.github/workflows/build.yml`, notamment le contrôle cryptographique de correspondance entre la clé privée et `cosign.pub`.
- [x] Valider `recipes/recipe.yml` avec le CLI BlueBuild (`bluebuild validate`) et générer un Containerfile (`bluebuild generate`) dans le workflow GitHub Actions.
- Vérifier la présence des trois logos, des trois vidéos et des deux fonds d'écran 4K aux chemins indiqués dans `branding/ASSET_MANIFEST.md`. Le workflow de validation contrôle la présence des flux vidéo/audio et décode intégralement les trois vidéos avec FFmpeg ; les SHA-256 de `branding/SHA256SUMS` identifient les originaux transmis dans la conversation et ne certifient pas les copies vidéo actuellement hébergées.
- Confirmer que le secret `SIGNING_SECRET` est configuré et que la clé publique correspondante est disponible.
- Déclencher le workflow manuellement seulement après ces contrôles.

La documentation BlueBuild recommande de valider/générer la recette avec son CLI avant de construire l'image. La compilation et surtout le premier démarrage doivent ensuite être testés sur une machine de test, jamais directement sur le seul poste de travail principal.

Références techniques : [format de recette BlueBuild](https://blue-build.org/reference/recipe/), [module systemd](https://blue-build.org/reference/modules/systemd/), [module copy](https://blue-build.org/reference/modules/copy/), [module DNF](https://blue-build.org/reference/modules/dnf/) et [FAQ Bazzite sur les variantes Desktop/Deck](https://docs.bazzite.gg/General/FAQ/).

## État des prérequis et validations restantes

- La clé publique `cosign.pub` est présente dans le dépôt ; le workflow a confirmé que le secret Actions `SIGNING_SECRET` lui correspond, sans exposer la clé privée.
- Les tests automatisés, le lint QML, les contrôles des ressources de marque et les précontrôles de signature ont réussi sur l'exécution de construction du 16 novembre 2026.
- Les trois images AMD/Intel, NVIDIA legacy et NVIDIA moderne ont été construites et publiées avec succès le 16 novembre 2026. Le tag vérifié pour les trois variantes est `e33a010-45` (run GitHub Actions `43933044510`). Les validations sur GPU réels restent à effectuer.
- Les logos, vidéos et fonds d'écran sont contrôlés automatiquement, mais leur rendu réel, la restitution vidéo/audio et les transitions doivent encore être validés sur une session Bazzite.
- Un démarrage de l’installateur dans une VM UEFI, une installation sur disque virtuel vierge et un premier démarrage de LEOS restent indispensables avant les essais physiques. L’ISO actuelle ouvre Anaconda ; le parcours observé ne fournit pas de bureau Live.

Le workflow `.github/workflows/build.yml` reste manuel. Il vérifie la présence des ressources officielles et les huit empreintes de `branding/DEPLOYED_SHA256SUMS`, puis effectue les tests et contrôles de signature avant d'appeler BlueBuild. Ces contrôles CI ne remplacent pas une validation matérielle.

## Pérennité du générateur ISO

La commande \`bluebuild generate-iso\` utilisée par notre workflow repose sur \`JasonN3/build-container-installer\`. Son dépôt amont a été archivé le 26 octobre 2026 et le mainteneur a déclaré le projet en fin de vie le 27 septembre 2026, en raison du changement d’outillage de génération d’images Fedora (Lorax vers Kiwi). La documentation BlueBuild confirme cette dépendance. Nous conservons temporairement la chaîne existante pour diagnostiquer l’ISO candidate, mais elle ne doit pas être considérée comme notre solution de publication à long terme.

La piste \`ublue-os/titanoboa\` sera évaluée séparément. Le projet vise une ISO Live pour images bootc et reste expérimental ; son contrat d’image et son flux d’installation ne sont pas présumés compatibles avec la base Bazzite/OSTree actuelle de LEOS. Aucune migration ne sera faite sans build, démarrage UEFI, installation sur disque virtuel vierge et test séparé de dual boot.

Les erreurs d’installation ne peuvent pas être attribuées au générateur sans journaux. En particulier, toute erreur pendant « Installation des logiciels » doit être diagnostiquée à partir de \`/tmp/packaging.log\` avant de modifier les recettes ou les paquets. Voir [Validation de l’ISO](iso-validation.md) pour les pistes connues et les références amont.

## Validation sur matériel réel

La checklist détaillée du premier démarrage, des transitions, du Bluetooth, des manettes, du Centre de contrôle, de la boutique et du rollback est disponible dans [la checklist de validation matérielle](hardware-validation.md). Elle doit être exécutée sur un PC de test avant de considérer l'image comme prête.

## Construction ISO

Le workflow manuel `.github/workflows/iso.yml` prépare cette étape à partir d'une image LEOS déjà publiée dans GHCR. Il demande explicitement la variante matérielle (standard, NVIDIA legacy ou NVIDIA moderne) et le tag exact de l'image ; aucun tag `latest` n'est supposé. C'est important car le workflow BlueBuild publie des tags propres à chaque exécution. Pour les trois images produites le 16 novembre 2026, le tag commun vérifié est `e33a010-45`. Le workflow vérifie d'abord la présence de `SIGNING_SECRET` et la correspondance cryptographique avec `cosign.pub`, puis valide le tag, télécharge l'image et prépare la génération. Avant toute vérification de signature, le workflow tire l'image sélectionnée avec Podman et résout son empreinte SHA-256. Cosign vérifie cette référence immuable `ghcr.io/...@sha256:...`. Une particularité de BlueBuild CLI 0.9.42 impose toutefois une précaution : son générateur ISO transforme une référence contenant uniquement un digest en tag `latest` pour `build-container-installer`. Le workflow conserve donc aussi le tag exact du build (`e33a010-45` pour les images actuelles), vérifie que ce tag pointe vers le digest signé juste avant la génération, puis revérifie le digest après la génération. Si le tag a changé, l'étape échoue et l'ISO n'est ni signée ni publiée. Le générateur reçoit ainsi le tag de build exact, jamais `latest`, tandis que la provenance conserve le digest vérifié et le tag utilisé.

La génération utilise explicitement le dossier `dist/iso` et s'arrête si ce dossier contient déjà des fichiers, afin de ne pas mélanger les résultats de plusieurs générations. Le workflow contrôle que l'ISO existe et n'est pas vide, produit puis vérifie sa somme SHA-256, et écrit le manifeste JSON de provenance dans le même dossier. Le manifeste distingue le commit du workflow ISO (`workflow_commit`) de l'image exacte utilisée (`source_image`, c'est-à-dire sa référence immuable avec digest), sans prétendre que le commit du workflow est nécessairement celui de l'image source.

Après la génération, le workflow signe l'ISO et le manifeste JSON de provenance avec la clé privée du secret Actions `SIGNING_SECRET`. Le script `.github/scripts/sign-iso-artifacts.sh` utilise une copie temporaire de la clé, limitée aux permissions `0600`, vérifie immédiatement les deux bundles avec `cosign.pub`, puis supprime son répertoire temporaire. Les bundles `.sigstore.json` de l'ISO et du manifeste sont ajoutés aux artefacts avec l'ISO, sa somme SHA-256 et le manifeste. Les artefacts GitHub Actions sont conservés pendant 14 jours.

Après téléchargement, vérifier les fichiers depuis le dossier qui contient l'ISO, le manifeste, les deux bundles Sigstore et le fichier SHA-256. Pour l'exemple de la variante standard avec le tag actuel `e33a010-45` :

```bash
sha256sum --check LEOS-standard-e33a010-45.iso.sha256
cosign verify-blob --key cosign.pub --bundle LEOS-standard-e33a010-45.iso.sigstore.json LEOS-standard-e33a010-45.iso
cosign verify-blob --key cosign.pub --bundle LEOS-standard-e33a010-45.iso.json.sigstore.json LEOS-standard-e33a010-45.iso.json
```

La somme SHA-256 contrôle l'intégrité du fichier ; la vérification Cosign établit que l'ISO et le manifeste ont été signés par la clé privée correspondant à la clé publique publiée dans le dépôt. Le secret `SIGNING_SECRET` doit donc être configuré pour le workflow ISO également. Ce workflow ne publie pas automatiquement une ISO et ne doit être lancé qu'après la réussite du build signé correspondant.

Cette méthode suit la documentation BlueBuild : générer l'ISO à partir de l'image publiée est le flux recommandé lorsque les images sont construites et publiées dans le cloud. Le workflow vérifie maintenant la somme SHA-256 et la présence d’une entrée UEFI dans le catalogue El Torito avec xorriso. Ce contrôle structurel ne démarre pas l’ISO : une vraie installation dans une VM UEFI, puis des essais physiques, restent obligatoires avant toute diffusion publique. Voir [le guide d'installation](installation.md) et [la procédure BlueBuild de génération ISO](https://blue-build.org/how-to/generate-iso/).
