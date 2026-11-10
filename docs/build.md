# Construire et vérifier LEOS

## État

La recette BlueBuild décrit une image basée sur Bazzite KDE Desktop. Le workflow de publication existe, mais une image LEOS n'a pas encore été compilée. Ne pas lancer de publication avant d'avoir configuré la signature et validé la recette.

## Base retenue

La recette utilise `ghcr.io/ublue-os/bazzite:stable`, c'est-à-dire la variante Desktop KDE de Bazzite. Elle correspond à notre choix : KDE reste le bureau, tandis que Gaming Mode est une application LEOS plein écran au-dessus de KDE. Nous ne sélectionnons pas l'image `bazzite-deck`, qui apporte sa propre session Steam Gaming Mode. La documentation Bazzite distingue bien les images Desktop sans Steam Gaming Mode des images Deck conçues pour démarrer dans cette session.

La variante Bazzite standard vise les GPU AMD/Intel ; les images NVIDIA sont séparées en variantes dédiées. Une variante NVIDIA LEOS devra donc être préparée et validée séparément avant de prétendre à une compatibilité NVIDIA complète.

## Contenu prévu de l'image

La recette ajoute les paquets Fedora `python3-pyside6` et `python3-psutil`, puis copie les dossiers Gaming, launcher, Control Center, core et branding dans `/usr/share/leos`. Elle installe les entrées KDE du sélecteur de modes et du Centre de contrôle, ainsi que l'autostart de session. Les noms de paquets sont publiés dans Fedora ; leur présence et leur compatibilité doivent tout de même être confirmées avec la version exacte de Bazzite utilisée pour le build.

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
- Vérifier la recette avec la version courante du CLI BlueBuild.
- Confirmer que le secret `SIGNING_SECRET` est configuré et que la clé publique correspondante est disponible.
- Déclencher le workflow manuellement seulement après ces contrôles.

La documentation BlueBuild recommande de valider/générer la recette avec son CLI avant de construire l'image. La compilation et surtout le premier démarrage doivent ensuite être testés sur une machine de test, jamais directement sur le seul poste de travail principal.

Références techniques : [format de recette BlueBuild](https://blue-build.org/reference/recipe/), [module copy](https://blue-build.org/reference/modules/copy/), [module DNF](https://blue-build.org/reference/modules/dnf/) et [FAQ Bazzite sur les variantes Desktop/Deck](https://docs.bazzite.gg/General/FAQ/).

## Construction ISO

L'ISO installable est une étape ultérieure. La priorité est d'abord de produire une image bootable signée, de la tester et de vérifier les mises à jour/rollback. La procédure ISO sera choisie après validation de l'image de base, en suivant le processus BlueBuild pour les images Fedora Atomic.
