# Installation de LEOS

## État actuel — 27 novembre 2026

La branche `main` est au commit `9fbd20506d727f05c632b6c31ee48f5adc73c44c` (PR #77 fusionnée après la finition graphique #75). La dernière correction synchronise le profil Desktop livré avec la palette graphite/argent partagée et ajoute un test qui protège cette cohérence.

- Validation de la PR #77 : 1 170 tests Python exécutés, 1 ignoré, aucun échec ; lint QML, BlueBuild, précontrôle et build de prévisualisation AMD/Intel réussis sur le commit candidat.
- Le build des trois images du commit précédent `29ac036` a réussi : AMD/Intel, NVIDIA legacy et NVIDIA moderne (run [#45988546222](https://github.com/jovanille43/LEOS/actions/runs/45988546222)).
- Le commit `9fbd205` a été fusionné ensuite. La reconstruction complète des trois images et la génération des ISO correspondantes doivent encore être vérifiées. Ne pas utiliser un ancien artefact pour valider la version graphique actuelle.
- Le workflow ISO [#45983444147](https://github.com/jovanille43/LEOS/actions/runs/45983444147), issu de `dc1faf7`, a terminé avec l'ISO standard réussie ; NVIDIA moderne a échoué à l'étape de démarrage UEFI/QEMU et NVIDIA legacy a échoué dès l'installation de Cosign (téléchargement HTTP 403). Ce lot précède les PR #75 et #77.
- Le dernier lot de trois ISO entièrement validé reste le run [#45855325068](https://github.com/jovanille43/LEOS/actions/runs/45855325068), basé sur `dcd8966). Les trois variantes y ont passé les contrôles de structure, checksum, digest, provenance et démarrage UEFI/QEMU jusqu'à Anaconda WebUI.
- La dernière installation interactive confirmée dans une VM date du 20 novembre 2026 et portait sur le commit antérieur `3c97827`. Elle ne valide pas le commit courant `9fbd205`.
- Un démarrage QEMU jusqu'à Anaconda WebUI ne constitue pas une installation complète. LEOS ne doit pas être présenté comme prêt à distribuer avant l'installation de la nouvelle ISO en VM, le contrôle de la première session et la validation de Desktop/Gaming après redémarrage.

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
5. Vérifier que l'installateur Anaconda WebUI s'ouvre, que la connexion réseau virtuelle est détectée et que la page de création du compte est proposée. Le générateur utilise volontairement le profil d'installateur Fedora Server pour laisser cette page visible ; cela ne change pas l'image cible, qui reste LEOS. Créer le compte dans Anaconda puis installer uniquement sur le disque virtuel. Si la page de création du compte est absente, arrêter le test et ne pas considérer l'ISO comme exploitable. Effectuer ensuite les contrôles KDE, réseau, audio et transitions Desktop/Gaming.
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
