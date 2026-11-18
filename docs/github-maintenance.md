# Entretien et gouvernance du dépôt GitHub LEOS

État observé le 18 novembre 2026. Cette page sépare les éléments déjà vérifiés des opérations qui nécessitent l'interface Settings de GitHub.

## Protection de `main`

Le dépôt ne présente actuellement aucune règle de protection de branche ni ruleset actif pour `main`. La branche peut donc recevoir un push direct. Les outils de gestion GitHub utilisés pour cette maintenance permettent de lire les règles mais pas de créer/modifier une ruleset ni de supprimer une référence de branche.

À configurer dans **Settings → Rules → Rulesets → New ruleset** :

1. Nom : `Protect main`.
2. Enforcement status : `Active`.
3. Target branches : inclure uniquement `main`.
4. Ne pas ajouter de bypass actor permanent.
5. Activer **Require a pull request before merging**.
6. Activer **Require status checks to pass** et sélectionner les contrôles GitHub Actions visibles sur une PR :
   - `python-checks` ;
   - `Validate LEOS image recipe`.
7. Activer **Block force pushes** et **Restrict deletions**.
8. Activer **Require conversation resolution** si cette option est disponible.
9. Ne pas imposer une approbation obligatoire d'un deuxième membre tant que le dépôt est géré par une seule personne ; cela risquerait de bloquer chaque PR.

Après création, vérifier que le ruleset apparaît comme actif et qu'un push direct vers `main` est refusé. La protection n'est pas effective tant que cette vérification n'a pas été faite.

## Description et sujets du dépôt

Dans **Settings → General**, utiliser la description proposée :

> LEOS is a Bazzite-based Linux distribution combining a customizable KDE desktop and a controller-first gaming experience.

Sujets GitHub recommandés :
`linux`, `linux-distribution`, `bazzite`, `bluebuild`, `fedora-atomic`, `kde-plasma`, `gaming`, `steam`, `qt6`, `qml`, `python`, `ostree`, `cosign`.

Ces métadonnées doivent être ajoutées dans la section About du dépôt ; elles ne sont pas modifiées par un commit Git.

## État des Pull Requests ouvertes

Les Pull Requests suivantes contiennent du travail fonctionnel ou des dépendances et doivent rester en brouillon jusqu'à revue et tests ciblés :

| PR | Objet | Dépendance / décision |
|---|---|---|
| #1 | Accessibilité Gaming | À conserver ; tester navigation et lecteur d'écran sur Bazzite |
| #2 | Design v2 et ressources transparentes | Base de travail de #3 et #6 |
| #3 | Emblèmes transparents | Dépend de la branche de #2 |
| #4 | Détection générique des manettes | À conserver ; revue du backend matériel puis essais contrôleurs |
| #6 | Fondations des thèmes A/B | Dépend de #2 ; comparer avec l'approche plus récente de #7 |
| #7 | Thèmes A/B et recoloration | À conserver en brouillon ; changement large qui nécessite une revue indépendante |
| #8 | Installateur alternatif Titanoboa | En attente ; la première ISO standard a déjà été générée par le workflow BlueBuild. Ne pas fusionner cette voie alternative avant de comparer les deux installateurs en VM |

La PR #5 sur la configuration initiale Cosign est remplacée par `docs/signing.md`, qui décrit le processus réellement déployé. Elle peut être fermée comme supersédée après la fusion de cette documentation.

La PR #18 a été fusionnée (documentation de l'ISO et guide VM). La PR #19 a été fusionnée (mise à jour des pages build/architecture/packaging). Les contrôles Python et BlueBuild sur ces PR ont réussi.

## Nettoyage des branches

Ne jamais supprimer une branche uniquement parce que son nom commence par `fix/` ou `docs/`. Supprimer seulement une branche dont la PR est fusionnée ou fermée, après avoir confirmé que son commit utile est présent dans `main` ou sauvegardé.

Branches de correctifs/documents déjà fusionnées qui peuvent être examinées pour suppression :
- `fix/build-cosign-preflight`
- `fix/build-recipe-paths`
- `fix/cosign-password-preflight`
- `fix/cosign-script-invocation`
- `fix/cosign-signing-check-main`
- `fix/cosign-v3-offline-key-check`
- `fix/iso-cosign-ignore-missing-tlog`
- `fix/iso-cosign-sudo-path`
- `fix/isolate-bluebuild-variants`
- `docs/first-iso-vm-validation`
- `docs/align-build-architecture-status`

Ne pas supprimer les branches actives associées aux PR #1, #2, #3, #4, #6, #7 et #8.

La suppression de références de branche et la configuration de rulesets nécessitent des permissions/actions administratives non exposées par les outils GitHub disponibles pour cette maintenance. Les branches listées sont candidates au nettoyage, pas des suppressions déjà réalisées.

## Releases

Aucune GitHub Release ni version taguée LEOS n'existe à ce jour. Le processus à suivre est décrit dans [release-process.md](release-process.md). Ne pas créer `v0.1.0` avant la validation VM et les tests physiques correspondants.
