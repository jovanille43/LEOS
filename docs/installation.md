# Installation de LEOS

## État actuel

LEOS est encore en développement. **Aucune image installable ni ISO LEOS n'est publiée à ce stade.** Ne tente pas d'installer les recettes de construction directement sur un ordinateur principal. La première image devra être construite, signée et testée sur une machine de test avant toute diffusion.

## Matériel et choix de l'image

LEOS vise les PC modernes x86_64 démarrant en UEFI. Le système conserve un seul ensemble de fonctions Desktop et Gaming ; les variantes ci-dessous ne changent que la base et les pilotes graphiques.

| Matériel graphique principal | Image à utiliser |
| --- | --- |
| AMD Radeon ou graphique intégré AMD | `leos` |
| Intel intégré ou Intel Arc | `leos` |
| NVIDIA Maxwell / Pascal / Volta | `leos-nvidia` |
| NVIDIA Turing ou génération plus récente | `leos-nvidia-open` |

Les GPU NVIDIA Kepler et plus anciens ne sont pas annoncés comme compatibles Gaming avec les pilotes propriétaires actuels de Bazzite. Les PC portables hybrides (iGPU + NVIDIA) devront être validés individuellement.

## Prérequis à vérifier

- Architecture x86_64.
- Démarrage UEFI ; le mode BIOS Legacy/CSM n'est pas pris en charge par la base ciblée.
- Disque cible : SSD interne, partitionnement GPT et au moins 50 Go libres (120 Go recommandés). Un disque actuellement partitionné en MBR n'est pas pris en charge par la base Bazzite.
- Sauvegarde complète : le partitionnement ou l'installation peut modifier ou effacer les partitions du disque choisi. Vérifie le modèle et la capacité du disque cible avant de confirmer toute opération.
- Le précontrôle matériel du Centre de contrôle LEOS est disponible après installation ; il ne vérifie pas à l'avance le disque choisi par l'installateur ni sa table GPT.
- Pour l'usage Gaming, prendre comme repère initial la référence publiée par Bazzite : 8 Go de RAM, processeur quadricœur à 2 GHz et GPU compatible Vulkan 1.3 ou supérieur.
- La prise en charge Wi-Fi, Bluetooth, audio, veille, écrans multiples et manettes dépend aussi des pilotes et périphériques présents.

Ces repères Gaming ne doivent pas être présentés comme des exigences universelles du mode Desktop. Un PC peut être utilisable en Desktop sans offrir les performances nécessaires aux jeux récents.

Le parcours du premier démarrage, y compris l'offre d'applications facultatives, est décrit dans le [guide de premier démarrage](first-run.md).

## Procédure prévue après publication

La procédure détaillée de retour arrière et de récupération est disponible dans [le guide de récupération](recovery.md). Lis-la avant le premier essai d'installation : LEOS repose sur les déploiements OSTree de Bazzite et ne fournit pas encore de mécanisme de réparation autonome.

1. Vérifier qu'une image LEOS signée a été publiée avec succès dans GHCR.
2. Dans GitHub Actions, lancer manuellement le workflow « Generate LEOS installer ISO » et choisir la variante matérielle ainsi que le tag de l'image publiée.
3. Récupérer l'ISO et son fichier SHA-256 dans les artefacts du workflow, puis vérifier la somme dans le même dossier avec `sha256sum --check LEOS-standard-latest.iso.sha256` (adapter le nom au fichier récupéré).
4. Sauvegarder les données importantes et préparer une clé USB d'installation avec Fedora Media Writer ; l'écriture de l'image efface le contenu de la clé choisie.
5. Démarrer la machine sur la clé en mode UEFI et choisir explicitement la variante correspondant au GPU principal.
6. Tester d'abord le démarrage live, l'affichage, le réseau, le son, le Bluetooth et les périphériques essentiels.
7. Avant toute installation, identifier précisément le disque cible (modèle et capacité), vérifier la sauvegarde et lire l'écran de partitionnement. Ne pas poursuivre si le disque ou les conséquences ne sont pas parfaitement compris.
8. Installer uniquement après validation du mode live et en ayant vérifié le disque cible. L'installation peut modifier ou effacer les partitions sélectionnées.
9. Au premier démarrage, vérifier que KDE, le réseau et le GPU fonctionnent avant de choisir Desktop ou Gaming depuis le sélecteur LEOS.
10. Les applications facultatives proposées par LEOS restent optionnelles : aucune installation ne sera effectuée sans confirmation.
11. Avant la première mise à jour, consulter le guide de récupération et vérifier qu'un déploiement précédent est disponible avec `rpm-ostree status`.

## Validation avant diffusion

Chaque variante doit être testée sur au moins une machine physique adaptée, puis sur une matrice élargie : PC de bureau, portable hybride, graphiques intégrés, GPU dédié, plusieurs écrans, Wi-Fi/Bluetooth, audio et manettes. Un build réussi ou un test sur une seule machine ne constitue pas une certification universelle.

Voir aussi :
- [Récupération et retour arrière](recovery.md)
- [Compatibilité matérielle](hardware-compatibility.md)
- [Matrice de validation](hardware-validation.md)
- [Construction et signature](build.md)
