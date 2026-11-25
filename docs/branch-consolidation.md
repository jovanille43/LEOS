# Consolidation des branches LEOS

Cette consolidation repart de `main` après la fusion de #64.

## Changements retenus

- #64 reste la référence pour le fond animé réutilisable et la navigation Desktop/Gaming.
- Les écrans Gaming et le sélecteur récupèrent les améliorations visuelles graphite/métal de #66 sans remplacer le fond partagé de #64.
- Les accents utilisateur A/B restent configurables et sont reliés par un dégradé discret dans Desktop, Gaming et le Centre de contrôle (#67).
- Les emblèmes transparents PNG sont des dérivés ; les fichiers JPEG sources sont conservés.
- Le premier démarrage expose un état des étapes ; les profils de dock existants reçoivent une fois le raccourci de changement de mode, sans rétablir un raccourci supprimé ensuite par l'utilisateur.
- Les tests conservent les contrats présents dans `main` et ajoutent les vérifications liées aux ressources transparentes et à la migration du dock.

## Périmètre volontairement exclu

- Le workflow ISO et le manifeste installateur ne sont pas modifiés par cette consolidation.
- L'installateur alternatif Titanoboa (#8) reste expérimental, sur sa branche dédiée.
- Les branches historiques divergentes ne sont pas fusionnées en bloc : leurs modifications doivent être réévaluées individuellement si elles apportent encore une fonctionnalité absente de `main`.

## Validation attendue

Les workflows Python checks, BlueBuild recipe checks et Build LEOS valident les sources et la recette. Ils ne prouvent pas à eux seuls qu'une ISO a été générée, démarrée en VM, installée sur disque puis validée après redémarrage.