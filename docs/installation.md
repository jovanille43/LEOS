# Installation de LEOS

## État actuel

LEOS est encore en développement. **Aucune image installable ni ISO LEOS n'est publiée à ce stade.** Ne tente pas d'installer les recettes de construction directement sur un ordinateur principal. La première image devra être construite, signée et testée sur une machine de test avant toute diffusion.

## Matériel et choix de l'image

LEOS vise les PC modernes x86_64 démarrant en UEFI. Le système conserve un seul ensemble de fonctions Desktop et Gaming ; les variantes ci-dessous ne changent que la base et les pilotes graphiques.

| Matériel graphique principal | Image à utiliser |
| --- | --- |
| AMD Radeon ou graphique intégré AMD | 'leos' |
| Intel intégré ou Intel Arc | 'leos' |
| NVIDIA Maxwell / Pascal / Volta | 'leos-nvidia' |
| NVIDIA Turing ou génération plus récente | 'leos-nvidia-open' |

Les GPU NVIDIA Kepler et plus anciens ne sont pas annoncés comme compatibles Gaming avec les pilotes propriétaires actuels de Bazzite. Les PC portables hybrides (iGPU + NVIDIA) devront être validés individuellement.

## Prérequis à vérifier

- Architecture x86_64.
- Démarrage UEFI ; le mode BIOS Legacy/CSM n'est pas pris en charge par la base ciblée.
- Espace disque suffisant sur SSD : prévoir au moins 50 Go libres, idéalement 120 Go.
- Pour l'usage Gaming, prendre comme repère initial la référence publiée par Bazzite : 8 Go de RAM, processeur quadricœur à 2 GHz et GPU compatible Vulkan 1.3 ou supérieur.
- La prise en charge Wi-Fi, Bluetooth, audio, veille, écrans multiples et manettes dépend aussi des pilotes et périphériques présents.

Ces repères Gaming ne doivent pas être présentés comme des exigences universelles du mode Desktop. Un PC peut être utilisable en Desktop sans offrir les performances nécessaires aux jeux récents.

## Procédure prévue après publication

1. Télécharger l'image correspondant au GPU principal depuis la publication officielle LEOS.
2. Vérifier la somme SHA-256 publiée avec l'image.
3. Sauvegarder les données importantes et préparer une clé USB d'installation.
4. Démarrer la machine sur la clé en mode UEFI.
5. Tester d'abord le démarrage, l'affichage, le réseau, le son, le Bluetooth et les périphériques essentiels.
6. Installer uniquement après validation de ces éléments et en ayant vérifié le disque cible.
7. Au premier démarrage, choisir Desktop ou Gaming depuis le sélecteur LEOS.
8. Les applications facultatives proposées par LEOS restent optionnelles : aucune installation ne sera effectuée sans confirmation.

## Validation avant diffusion

Chaque variante doit être testée sur au moins une machine physique adaptée, puis sur une matrice élargie : PC de bureau, portable hybride, graphiques intégrés, GPU dédié, plusieurs écrans, Wi-Fi/Bluetooth, audio et manettes. Un build réussi ou un test sur une seule machine ne constitue pas une certification universelle.

Voir aussi :
- [Compatibilité matérielle](hardware-compatibility.md)
- [Matrice de validation](hardware-validation.md)
- [Construction et signature](build.md)
