# Chaîne d’installation Live LEOS avec Titanoboa

## Statut actuel

Cette chaîne est une candidate expérimentale développée sur la branche feature/titanoboa-installer. Elle n’a pas encore produit une ISO validée et ne doit pas être utilisée sur le PC principal. L’ancien workflow iso.yml est conservé intact comme référence de comparaison et solution de repli.

Titanoboa est présenté par son projet comme un constructeur expérimental d’ISO Live pour images bootc. LEOS reprend l’architecture du workflow Bazzite : une image Live KDE est préparée à partir de Bazzite, l’image LEOS à installer est embarquée dans le stockage Podman du Live, puis Titanoboa produit l’ISO. Références amont : https://github.com/ublue-os/titanoboa, le workflow ISO de Bazzite et ses scripts d’installation.

## Flux de construction

1. Le workflow sélectionne explicitement une variante LEOS et un tag publié.
2. Le script de préparation résout le digest SHA-256 immuable de l’image.
3. Cosign vérifie la signature de l’image publiée avant qu’elle soit intégrée au média.
4. Le workflow résout le digest de ghcr.io/ublue-os/bazzite:stable et construit l’image Live KDE depuis cette référence immuable ; le manifeste conserve le tag et le digest de la base.
5. Le constructeur Live tire l’image LEOS par digest, lui donne un nom local pour Anaconda et compare l’identifiant de l’image après export/import.
6. Titanoboa construit l’ISO. Le workflow vérifie ensuite le SHA-256, le catalogue UEFI, la signature et le manifeste de provenance.

Le secret SIGNING_SECRET reste exclusivement dans GitHub Actions. La clé privée de signature n’est ni copiée dans l’image Live, ni enregistrée dans le dépôt, ni incluse dans l’ISO.

Le workflow exécute maintenant `.github/scripts/verify-live-installer-image.sh` juste après la construction de l’image Live et avant Titanoboa. Ce précontrôle monte l’image avec Podman et vérifie la présence d’un seul noyau, de son initramfs, des modules GRUB PC, des binaires EFI Fedora dans les deux emplacements attendus par le contrat, du fichier `iso.yaml` et des métadonnées/du stockage Podman qui embarquent l’image LEOS. Ce contrôle statique ne remplace pas un démarrage de l’ISO : il prouve seulement que l’image source contient les éléments nécessaires au générateur.

### Pourquoi conserver le parcours Anaconda actuel

La directive Kickstart native `bootc` de Fedora 43+ sait séparer la référence source de l’image cible utilisée pour les mises à jour, mais LEOS ne l’utilise pas avec `ostreecontainer`. La documentation Image Builder signale un échec possible de `systemd-remount-fs.service` sur des systèmes bootc installés par Anaconda. Le ticket Anaconda [Bugzilla 2332319](https://bugzilla.redhat.com/show_bug.cgi?id=2332319) indique un correctif dans `anaconda-dracut` 46.6-1.fc46. Comme la base LEOS est Bazzite/Fedora 45, le hook met à niveau `anaconda-core`, `anaconda-live` et `anaconda-dracut`, puis vérifie que le changelog du paquet `anaconda-dracut` mentionne le correctif 2332319. Si le correctif n’est pas détecté, la construction de l’image Live s’arrête et aucune ISO candidate n’est produite avec cette version d’Anaconda. LEOS conserve le parcours Bazzite (`ostreecontainer` sur le stockage local, puis `bootc switch` avec signature obligatoire) et ne revendique pas la validité de la directive Kickstart `bootc` native sur Fedora 45.

## Déploiement Anaconda

Anaconda déploie d’abord l’image LEOS embarquée via ostreecontainer et le transport containers-storage. Le déploiement initial utilise donc le contenu déjà vérifié et présent dans le Live, sans télécharger à nouveau l’image complète pendant la phase OSTree. Le hook revalide aussi que la référence taguée et le digest embarqué désignent le même dépôt, puis compare le digest réellement visible dans le stockage Podman au digest enregistré pendant la génération de l’ISO ; sinon l’installation s’arrête.

Un bootc switch final utilise ensuite la référence GHCR taguée comme origine des futures mises à jour et exige la politique de signature des conteneurs. L’image intégrée au Live reste, elle, vérifiée par digest immuable. Les trois dépôts LEOS (standard, NVIDIA legacy et NVIDIA open) sont associés à la clé publique LEOS ; les autres images de conteneurs conservent le comportement par défaut standard pour ne pas empêcher des usages comme Distrobox.

Le profil Anaconda conserve le chemin EFI standard `EFI/fedora`, comme Bazzite, pour rester cohérent avec son intégration bootc/bootupd. Sur une installation Ubuntu existante, `EFI/ubuntu` est distinct et les hooks LEOS ne le suppriment pas. Ils ne suppriment pas non plus `EFI/fedora`, ne renomment pas de partition `/boot` et ne lancent aucune commande de formatage ou d’effacement de disque. Un système Fedora déjà présent pourrait toutefois partager ce chemin : le dual boot n'est donc pas garanti. Le partitionnement choisi dans Anaconda doit encore être testé et validé. Le précontrôle vérifie aussi qu’Anaconda a monté une partition `/boot` dédiée en ext4, distincte de `/boot/efi` ; sinon l’installation s’interrompt avant le déploiement. Il ne renomme pas le label de cette partition. Pour un essai avec Ubuntu, il faudra créer ce `/boot` ext4 séparément dans l’espace libre et réutiliser l’ESP existante sans la formater ; ce scénario reste à valider en VM.

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
