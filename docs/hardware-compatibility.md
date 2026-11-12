# Compatibilité matérielle LEOS

## Objectif

LEOS doit fonctionner sur un large éventail de PC fixes et portables, sans être lié à une configuration CPU/GPU précise. La compatibilité dépend toutefois de la base Bazzite, du noyau Linux, des pilotes disponibles et du matériel réellement pris en charge. **« Tous les ordinateurs » ne peut pas être garanti.**

La cible de la première version est un PC **x86_64 démarrant en UEFI**. Les architectures ARM et le démarrage BIOS Legacy/CSM ne font pas partie de la cible actuelle, car LEOS hérite des contraintes de sa base Bazzite.

Trois recettes de construction sont prévues à partir d'une liste de modules LEOS partagée : `leos` pour Bazzite standard (AMD/Intel), `leos-nvidia` pour les anciennes générations NVIDIA encore prises en charge par le pilote propriétaire legacy, et `leos-nvidia-open` pour les générations NVIDIA récentes. Ce sont trois variantes matérielles du même système LEOS, pas trois éditions fonctionnelles différentes. Le choix de l'image doit être fait selon le GPU principal ; il ne sera pas décidé silencieusement par LEOS pendant l'installation.

## Référence minimale pour Gaming

Le guide matériel Bazzite indique actuellement, pour le jeu :

- processeur quadricœur à 2 GHz ou supérieur ;
- 8 Go de RAM ;
- GPU capable d'utiliser Vulkan 1.3 ou supérieur ;
- 50 Go libres sur un SSD interne (120 Go recommandés) ;
- firmware UEFI ; le démarrage CSM/Legacy n'est pas pris en charge.

Ces chiffres sont la référence publiée par Bazzite pour Gaming, pas une promesse de performances LEOS. Un PC sous ces seuils peut éventuellement démarrer un environnement Linux ou afficher le bureau, mais il ne doit pas être présenté comme une configuration Gaming officiellement validée.

Référence : [Bazzite — Hardware Compatibility for Linux Gaming](https://docs.bazzite.gg/Gaming/Hardware_compatibility_for_gaming/).

## Prise en charge graphique

LEOS vise les PC équipés de GPU AMD, Intel ou NVIDIA, mais les modalités de prise en charge ne sont pas identiques :

- **AMD** : priorité de validation pour l'expérience Gaming, avec les pilotes Mesa/kernel fournis par la base.
- **Intel** : iGPU et cartes Arc à tester selon génération et prise en charge Vulkan ; ne pas assimiler toutes les générations aux mêmes capacités.
- **NVIDIA** : nécessite de sélectionner la variante Bazzite adaptée à la génération du GPU. `leos-nvidia` (`ghcr.io/ublue-os/bazzite-nvidia`) cible les architectures Maxwell, Pascal et Volta (notamment GTX 900/1000 et Titan V). `leos-nvidia-open` (`ghcr.io/ublue-os/bazzite-nvidia-open`) cible Turing et les générations plus récentes (GTX 16 et RTX). Les deux recettes réutilisent exactement les mêmes modules LEOS que la variante standard. Les GPU Kepler et plus anciens ne disposent plus du pilote propriétaire NVIDIA pris en charge par Bazzite ; ils ne doivent donc pas être annoncés comme compatibles Gaming. Les variantes NVIDIA doivent encore être construites et testées sur des GPU réels avant de revendiquer une prise en charge complète.

Bazzite signale des réserves plus importantes pour NVIDIA que pour AMD et des réserves plus limitées pour Intel Arc. Le choix de l'image Bazzite dépend du fabricant du GPU principal. Références : [guide de compatibilité Bazzite](https://docs.bazzite.gg/Gaming/Hardware_compatibility_for_gaming/) et [dépôt officiel Bazzite](https://github.com/ublue-os/bazzite).

Les PC portables hybrides (iGPU + GPU dédié) devront être testés séparément : affichage sur l'iGPU, lancement des jeux sur le GPU dédié, veille/réveil et écrans externes. LEOS ne doit jamais supposer qu'un GPU est actif uniquement parce qu'il apparaît dans l'inventaire.

## Adaptation logicielle

- La télémétrie NVIDIA est associée au périphérique DRM par son identifiant PCI (domain:bus:device.function), jamais par l'ordre des lignes de `nvidia-smi` ou le numéro `cardN`.
- Sur une configuration hybride ou avec plusieurs GPU, les mesures NVIDIA ne sont fusionnées qu'avec la carte dont l'identifiant PCI correspond exactement. En l'absence de correspondance, les mesures restent indisponibles plutôt que d'être attribuées à une autre carte.
- Si `nvidia-smi`, le pilote propriétaire ou l'accès aux nœuds DRM est absent ou expire, la télémétrie est facultative et ne doit pas empêcher Gaming Mode de démarrer.

La détection matérielle doit rester non bloquante et tolérante aux fonctions absentes :

- l'absence d'un capteur ne doit pas faire échouer l'interface ;
- une donnée non exposée par le pilote reste « indisponible », jamais simulée ;
- les animations, effets et rafraîchissements peuvent être allégés sur les machines modestes ;
- les fonctions spécifiques à un fournisseur ne sont activées que si leur outil ou leur interface est réellement disponible ;
- sur un système multi-GPU, l'inventaire identifie chaque carte PCI lorsque les informations sont exposées ; la télémétrie Gaming privilégie le GPU qui fournit les mesures réelles les plus complètes ;
- les températures privilégient les capteurs CPU/GPU identifiés plutôt que les sondes génériques du châssis ou des périphériques ;
- la configuration matérielle ne doit pas déclencher silencieusement l'installation ou la suppression d'un pilote.

Le précontrôle affiché dans **Centre de contrôle → Matériel & connexions** vérifie l'architecture, le mode de démarrage, la quantité de RAM, une estimation des cœurs physiques, l'espace libre sur la racine / et la version Vulkan exposée par chaque GPU. LEOS inclut le paquet `vulkan-tools` pour fournir `vulkaninfo` ; la mesure reste « non vérifiable » si le pilote ou l'interface Vulkan n'expose pas les informations attendues. Le contrôle compare ces informations aux repères Gaming Bazzite (4 cœurs, 8 Go, 50 Go libres et Vulkan 1.3+). Il reste indicatif : la fréquence CPU de référence, le type et l'emplacement physique du SSD, la table GPT, la compatibilité réelle des pilotes, du Wi-Fi, du Bluetooth, de l'audio et des périphériques ne sont pas certifiés. L'absence d'une donnée, ou l'échec de la sonde Vulkan, est signalée comme « non vérifiable » et ne bloque jamais Desktop Mode.

## Matrice de validation avant publication

Chaque variante d'image doit être testée sur du matériel réel, au minimum avec :

1. PC AMD (CPU et GPU Radeon), PC Intel avec iGPU, PC Intel Arc et PC NVIDIA ;
2. PC portable hybride AMD/Intel + NVIDIA et plusieurs écrans ;
3. Wi-Fi, Ethernet, Bluetooth, audio intégré, USB, manettes Xbox/PlayStation/Nintendo ;
4. veille/réveil, changement de résolution/fréquence, accélération vidéo, Vulkan et lancement de jeux ;
5. installation propre, mise à jour, rollback et récupération après échec.

Une image qui compile ou passe les tests automatisés n'est pas pour autant certifiée sur ces machines. La compatibilité doit être publiée par modèle/configuration testés, avec les limites connues.

## Limites de la première version

- Cible actuelle : x86_64 + UEFI.
- Les recettes standard, NVIDIA legacy et NVIDIA open existent dans le dépôt ; leur construction, la signature et les essais matériels restent à réaliser.
- Le précontrôle Gaming mesure les capacités exposées par Linux, mais ne remplace pas l'inspection du support cible ni les essais physiques.
- Aucune liste exhaustive de PC compatibles n'est revendiquée.
- La construction d'une ISO installable et la validation sur plusieurs ordinateurs restent à effectuer.
