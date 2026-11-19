# Installation de LEOS

## État actuel — 19 novembre 2026

La première **ISO installateur LEOS standard** a été générée avec succès par GitHub Actions après vérification de la signature de l'image publiée.

- Artefact GitHub Actions : `LEOS-installer-standard-latest`.
- Fichier ISO attendu dans l'archive : `LEOS-standard-latest.iso`.
- Historique des générations : [workflow Generate LEOS installer ISO](https://github.com/jovanille43/LEOS/actions/workflows/iso.yml).
- N'utiliser qu'un artefact provenant d'une exécution qui a terminé avec succès l'étape **Validate ISO boot structure, checksum, and source digest**.
- Les trois images conteneur (standard AMD/Intel, NVIDIA legacy et NVIDIA open) ont été construites, publiées et signées dans GHCR.
- À ce stade, seule la variante ISO **standard** a été générée. Les variantes ISO NVIDIA restent à produire.
- L'ISO reste un artefact de validation, pas une version stable certifiée. Les contrôles structurels automatisés ne remplacent pas un démarrage et une installation testés dans une machine virtuelle, puis des essais matériels.

Commencer par une machine virtuelle et ne jamais sélectionner le disque du PC hôte. La validation matérielle réelle viendra après les essais VM.

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

## Première validation — machine virtuelle

La première étape est décrite dans le [guide de validation en machine virtuelle](virtual-machine-validation.md). Elle permet de vérifier le démarrage et le parcours d'installation sans toucher aux partitions du PC hôte.

1. Ouvrir l'historique du workflow ISO et choisir la dernière exécution réussie déclenchée par un **push sur `main`** ou par un lancement manuel (`workflow_dispatch`), jamais une exécution `pull_request`. Vérifier que les étapes **Validate ISO boot structure, checksum, and source digest**, **Boot installer ISO with UEFI firmware in QEMU** et **Upload installer ISO and checksum** ont réussi, puis télécharger l'artefact `LEOS-installer-standard-latest` et extraire l'archive ZIP. Les exécutions de pull request valident l'ISO mais ignorent volontairement l'envoi de l'artefact.
2. Vérifier l'ISO avec `sha256sum --check LEOS-standard-latest.iso.sha256`, depuis le dossier contenant les deux fichiers.
3. Créer une machine virtuelle UEFI avec un disque virtuel dédié ; ne jamais connecter un disque physique de l'hôte.
4. Démarrer sur l'ISO, vérifier l'environnement proposé, puis installer uniquement sur le disque virtuel de la VM.
5. Vérifier que l'installateur Anaconda WebUI s'ouvre, que la connexion réseau virtuelle est détectée, puis installer uniquement sur le disque virtuel. Effectuer ensuite les contrôles KDE, réseau, audio et transitions Desktop/Gaming.
6. Consigner les anomalies et conserver l'ISO ainsi que le fichier SHA-256 utilisés.

## Validation sur matériel physique

La procédure physique vient **après** la validation VM. La procédure détaillée de retour arrière et de récupération est disponible dans [le guide de récupération](recovery.md). Lis-la avant tout essai sur un PC de test.

1. Sauvegarder les données et préparer un support de récupération connu comme fonctionnel.
2. Choisir explicitement la variante correspondant au GPU principal.
3. Démarrer sur la clé USB en mode UEFI et tester le démarrage, l'affichage, le réseau, le son, le Bluetooth et les périphériques essentiels.
4. Avant toute installation, identifier précisément le disque cible (modèle et capacité), vérifier la sauvegarde et lire l'écran de partitionnement. Ne pas poursuivre si le disque ou les conséquences ne sont pas parfaitement compris.
5. Installer uniquement sur un PC ou un disque de test, après validation du mode live et du disque cible.
6. Au premier démarrage, vérifier KDE, le réseau et le GPU avant de choisir Desktop ou Gaming.
7. Les applications facultatives proposées par LEOS restent optionnelles : aucune installation ne sera effectuée sans confirmation.
8. Avant la première mise à jour, consulter le guide de récupération et vérifier qu'un déploiement précédent est disponible avec `rpm-ostree status`.

## Validation avant diffusion

Chaque variante doit être testée sur au moins une machine physique adaptée, puis sur une matrice élargie : PC de bureau, portable hybride, graphiques intégrés, GPU dédié, plusieurs écrans, Wi-Fi/Bluetooth, audio et manettes. Un build réussi ou un test sur une seule machine ne constitue pas une certification universelle.

Voir aussi :
- [Récupération et retour arrière](recovery.md)
- [Compatibilité matérielle](hardware-compatibility.md)
- [Matrice de validation](hardware-validation.md)
- [Construction et signature](build.md)
