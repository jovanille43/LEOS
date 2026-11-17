# Installation de LEOS

## État au 17 novembre 2026

Les trois images LEOS (standard AMD/Intel, NVIDIA legacy et NVIDIA open) ont été construites et signées dans GHCR avec le tag e33a010-45 (workflow 43933044510). Une ISO installateur **standard** a été générée et signée (workflow 43946765765). Les ISO NVIDIA doivent encore être générées.

Cette ISO est une image d’installation basée sur l’installateur Fedora/Anaconda. Le menu observé propose « Install LEOS » et « Test this media & install LEOS » ; ce dernier contrôle le support avant d’ouvrir l’installateur. **Ce parcours ne démarre pas un bureau LEOS en session Live.**

La première validation physique n’a pas abouti : le contrôle média a affiché FAIL et une tentative d’installation a ensuite échoué pendant l’étape « Installation des logiciels ». La cause n’est pas établie. Le fichier ISO téléchargé et la clé USB doivent être contrôlés avant tout nouvel essai. Ne considère pas un build GitHub réussi comme une preuve qu’une installation fonctionne.

## Nouvelle chaîne Live Titanoboa — candidate, non validée

La branche `feature/titanoboa-installer` contient une nouvelle chaîne expérimentale : elle construit un environnement Live KDE à partir de Bazzite, y embarque l'image LEOS cible, puis génère l'ISO avec Titanoboa. Anaconda déploie l'image embarquée, puis vérifie sa signature en revenant à sa référence GHCR. Le profil déclare un répertoire EFI `leos` et les hooks LEOS ne suppriment pas les dossiers EFI d'autres systèmes.

**Important :** les images précédemment publiées avec le tag `e33a010-45` ne contiennent pas la nouvelle politique de signatures installée par cette branche. Il faut d'abord relancer le workflow **Build LEOS** sur `feature/titanoboa-installer` pour publier trois nouvelles images signées, puis utiliser le workflow **Generate LEOS Titanoboa Live installer ISO** avec le tag correspondant. Ne lance pas l'ancien tag avec le nouveau workflow.

Cette chaîne n'a pas encore été construite ni démarrée dans une VM. Elle n'est pas prête pour une installation sur le ThinkPad. L'installation automatique ou le dual boot ne sont pas garantis ; le partitionnement doit rester vérifié à la main. Voir [l'architecture et les critères de validation Titanoboa](titanoboa-installer.md).

## Matériel et variante

LEOS cible les PC x86_64 démarrant en UEFI. Les variantes partagent les mêmes fonctions Desktop et Gaming ; seule la base et la pile graphique varient.

| Matériel graphique principal | Image |
| --- | --- |
| AMD Radeon ou graphique intégré AMD | leos (standard) |
| Intel intégré ou Intel Arc | leos (standard) |
| NVIDIA Maxwell / Pascal / Volta | leos-nvidia (legacy) |
| NVIDIA Turing ou génération plus récente | leos-nvidia-open |

Les GPU NVIDIA Kepler et plus anciens ne sont pas annoncés comme compatibles Gaming avec les pilotes actuels de Bazzite. Les portables hybrides iGPU + NVIDIA doivent être validés individuellement. Choisis la variante correspondant au GPU principal ; ne suppose pas que l’installateur la détectera automatiquement.

## Prérequis

- Architecture x86_64 et démarrage UEFI ; le mode BIOS Legacy/CSM n’est pas dans la cible actuelle.
- Disque GPT ; repère de stockage Gaming : au moins 50 Go libres sur SSD interne, 120 Go recommandés. La capacité réellement nécessaire doit être contrôlée pour la version de l’image installée.
- Sauvegarde complète sur un support distinct.
- Identification certaine du disque cible par modèle et capacité.
- Pour tout essai d’installation, privilégier une machine ou un disque de test. Ne pas utiliser le seul ordinateur principal.
- La vérification matérielle dans le Centre de contrôle intervient après installation ; elle ne valide pas le disque cible, la table GPT ni le schéma de partitions de l’installateur.

Les repères Gaming ne sont pas des exigences universelles du mode Desktop. Wi-Fi, Bluetooth, audio, veille, écrans et manettes dépendent des pilotes et périphériques réellement présents.

## Vérifier l’ISO avant de préparer la clé

Télécharge l’ISO et tous les fichiers annexes depuis le même artefact GitHub Actions. Depuis le dossier extrait, vérifie d’abord la somme SHA-256. Exemple pour l’ISO standard candidate :

~~~bash
sha256sum --check LEOS-standard-e33a010-45.iso.sha256
~~~

Puis vérifie la signature de l’ISO et celle du manifeste de provenance avec la clé publique cosign.pub du dépôt :

~~~bash
cosign verify-blob --key cosign.pub --bundle LEOS-standard-e33a010-45.iso.sigstore.json LEOS-standard-e33a010-45.iso
cosign verify-blob --key cosign.pub --bundle LEOS-standard-e33a010-45.iso.json.sigstore.json LEOS-standard-e33a010-45.iso.json
~~~

Adapte les noms à la variante et au tag récupérés. Si la somme SHA-256 ou une signature échoue, **n’écris pas l’ISO sur une clé USB** : télécharge à nouveau l’artefact et recommence les contrôles. La clé cosign.pub est publique ; ne demande ni ne copie jamais la clé privée.

La CI inspecte aussi le catalogue d’amorçage El Torito et vérifie la présence d’une entrée UEFI. Ce contrôle statique confirme la présence d’une structure d’amorçage UEFI dans l’ISO ; il ne remplace pas un vrai démarrage en machine virtuelle.

## Préparer et contrôler la clé USB

Utilise de préférence Fedora Media Writer ou un outil fiable d’écriture brute. L’écriture efface entièrement la clé sélectionnée. Identifie le périphérique USB avec lsblk et vérifie son modèle et sa capacité ; ne sélectionne jamais le SSD interne.

Après l’écriture et la synchronisation, compare si possible l’empreinte des premiers octets écrits sur le périphérique avec celle de l’ISO. Exemple en remplaçant /dev/sdX par **le disque USB entier**, jamais une partition :

~~~bash
ISO=LEOS-standard-e33a010-45.iso
DEVICE=/dev/sdX
ISO_SIZE=$(stat -c '%s' "$ISO")
sha256sum "$ISO"
sudo head -c "$ISO_SIZE" "$DEVICE" | sha256sum
~~~

Les deux empreintes SHA-256 doivent être identiques. Cette lecture ne modifie pas la clé. Si elles diffèrent, ne démarre pas dessus : réécris la clé ou essaie un autre support/port USB.

Au démarrage, sélectionne l’entrée USB en mode UEFI. Le choix « Test this media & install LEOS » lance le contrôle du média. Si le résultat est FAIL, arrête le test : ne contourne pas l’avertissement pour installer. Vérifie de nouveau l’ISO et la lecture USB ; si les empreintes correspondent encore, conserve les journaux et investigue le problème au lieu de multiplier les tentatives.

Pour le détail de cette procédure, voir [Validation de l’ISO et du support USB](iso-validation.md).

## Installation et dual boot

**L’installation en dual boot n’est pas encore validée ni garantie par LEOS.** L’installateur peut proposer des opérations de partitionnement qui modifient le disque choisi. Ne valide pas le partitionnement automatique sur un disque qui contient déjà Ubuntu, Windows ou des données importantes.

Jusqu’à la validation dédiée :
1. teste d’abord l’installateur dans une machine virtuelle UEFI avec un disque virtuel vierge ;
2. réalise ensuite les premiers essais physiques sur un disque de test ou une machine secondaire ;
3. pour tester le dual boot, utilise une machine virtuelle jetable contenant un autre système et un espace non alloué ;
4. vérifie chaque partition, son système de fichiers, son point de montage et l’option de formatage avant d’appliquer les changements.

Ne formate jamais la partition EFI existante d’un système que tu souhaites conserver. Ne redimensionne pas une partition depuis l’installateur sans procédure confirmée et sauvegarde vérifiée. Si l’écran ne permet pas de distinguer clairement l’espace libre des partitions existantes, annule et demande un diagnostic. N’invente pas de point de montage : le schéma exact doit être confirmé pour la version de l’installateur.

## En cas d’échec de l’installateur

Ne relance pas immédiatement l’installation. Note l’étape exacte, le texte intégral de l’erreur et l’opération qui venait de se produire. Pour un blocage pendant « Installation des logiciels », récupère si disponibles les journaux Anaconda suivants depuis l’installateur ou son terminal :

- /tmp/anaconda.log
- /tmp/packaging.log
- /tmp/program.log
- /tmp/storage.log
- /tmp/syslog
- journalctl -b

Ne partage que les extraits utiles et masque les noms d’utilisateur, chemins personnels, adresses IP publiques et identifiants. Ces journaux permettent de distinguer un problème de lecture du support, de stockage, de téléchargement de métadonnées ou de déploiement.

## Validation après installation

Sur une machine de test, confirme que le système démarre, que KDE s’ouvre, que le réseau fonctionne et que la variante GPU attendue est chargée. Vérifie ensuite les services et l’état OSTree :

~~~bash
rpm-ostree status
uname -r
cat /etc/os-release
systemctl --failed
systemctl --user --failed
~~~

La compatibilité doit être consignée pour chaque configuration testée. Un build réussi, une somme correcte ou un démarrage de l’installateur ne certifient pas à eux seuls l’installation complète ni tous les PC.

Voir aussi :
- [Validation de l’ISO et du support USB](iso-validation.md)
- [Récupération et retour arrière](recovery.md)
- [Compatibilité matérielle](hardware-compatibility.md)
- [Matrice de validation](hardware-validation.md)
- [Construction et signature](build.md)
