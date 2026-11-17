# Chaîne d’installation Live LEOS avec Titanoboa

## Statut actuel

Cette chaîne est une candidate expérimentale développée sur la branche feature/titanoboa-installer. Elle n’a pas encore produit une ISO validée et ne doit pas être utilisée sur le PC principal. L’ancien workflow iso.yml est conservé intact comme référence de comparaison et solution de repli.

Titanoboa est présenté par son projet comme un constructeur expérimental d’ISO Live pour images bootc. LEOS reprend l’architecture du workflow Bazzite : une image Live KDE est préparée à partir de Bazzite, l’image LEOS à installer est embarquée dans le stockage Podman du Live, puis Titanoboa produit l’ISO. Références amont : https://github.com/ublue-os/titanoboa, le workflow ISO de Bazzite et ses scripts d’installation.

## Flux de construction

1. Le workflow sélectionne explicitement une variante LEOS et un tag publié.
2. Le script de préparation résout le digest SHA-256 immuable de l’image.
3. Cosign vérifie la signature de l’image publiée avant qu’elle soit intégrée au média.
4. Une image Live KDE est construite à partir de ghcr.io/ublue-os/bazzite:stable.
5. Le constructeur Live tire l’image LEOS par digest, lui donne un nom local pour Anaconda et compare l’identifiant de l’image après export/import.
6. Titanoboa construit l’ISO. Le workflow vérifie ensuite le SHA-256, le catalogue UEFI, la signature et le manifeste de provenance.

Le secret SIGNING_SECRET reste exclusivement dans GitHub Actions. La clé privée de signature n’est ni copiée dans l’image Live, ni enregistrée dans le dépôt, ni incluse dans l’ISO.

## Déploiement Anaconda

Anaconda déploie d’abord l’image LEOS embarquée via ostreecontainer et le transport containers-storage. Le déploiement initial utilise donc le contenu déjà vérifié et présent dans le Live, sans télécharger à nouveau l’image complète pendant la phase OSTree.

Un bootc switch final utilise ensuite la référence GHCR par digest et exige la politique de signature des conteneurs. Les trois dépôts LEOS (standard, NVIDIA legacy et NVIDIA open) sont associés à la clé publique LEOS ; les autres images de conteneurs conservent le comportement par défaut standard pour ne pas empêcher des usages comme Distrobox.

Le profil Anaconda utilise un dossier EFI distinct, EFI/leos. Les hooks LEOS ne suppriment pas EFI/fedora, ne renomment pas de partition /boot et ne lancent aucune commande de formatage ou d’effacement de disque. Cela réduit le risque d’écraser une entrée de démarrage existante, mais ne constitue pas une garantie de dual boot : le partitionnement choisi dans Anaconda doit encore être testé et validé.

## Journaux en cas d’échec

Le bloc %onerror récupère, lorsqu’ils existent, les journaux suivants : anaconda.log, packaging.log, program.log, storage.log et syslog. Il prépare l’archive LEOS-installation-diagnostics.tar.gz sur le bureau de la session Live et tente d’afficher un résumé avec YAD.

Les journaux peuvent contenir des informations personnelles ou des chemins privés. Il faut les inspecter et les expurger avant de les partager.

## Validation obligatoire

- Les trois recettes BlueBuild doivent passer la validation.
- Les scripts shell doivent passer bash -n et les tests de contrat Python.
- Le workflow Titanoboa doit réellement construire l’image Live et l’ISO.
- xorriso doit confirmer le catalogue UEFI ; SHA-256 et signatures doivent être valides.
- L’ISO doit démarrer dans une VM x86_64 en UEFI.
- Anaconda doit s’ouvrir et installer l’image sur un disque virtuel vierge.
- Le système installé doit redémarrer et passer les contrôles bootc status, réseau, KDE et services.
- Le dual boot doit être testé séparément dans une VM jetable contenant un autre système UEFI et des partitions existantes.

Un build réussi ou des tests statiques verts ne prouvent pas une installation réussie. Aucune nouvelle tentative sur le ThinkPad ne doit avoir lieu tant que le démarrage et l’installation dans la VM ne sont pas validés, puis que le fichier ISO et la clé USB n’ont pas été contrôlés par SHA-256.
