# Première validation LEOS en machine virtuelle

## Résultat confirmé — 20 novembre 2026

La première installation interactive de l'ISO standard a abouti dans une machine virtuelle QEMU/KVM :
- l'écran Anaconda de création du compte utilisateur a été présenté et le compte a été créé ;
- l'installation s'est terminée et la machine a redémarré depuis son disque virtuel ;
- la connexion KDE a fonctionné et la session Plasma est arrivée jusqu'au bureau ;
- `rpm-ostree status` a identifié l'image déployée comme `ostree-image-signed:docker://ghcr.io/jovanille43/leos:latest`.

L'ISO utilisée provenait de l'exécution [Generate LEOS installer ISO #44729268412](https://github.com/jovanille43/LEOS/actions/runs/44729268412), basée sur le commit `3c97827f5c658ed246a7b96ed4a5e8e1fbb2f317`. Le statut rpm-ostree photographié par l'utilisateur affichait le digest `sha256:83a710a01526c94e1b637a72ef8f74f96e3da58b45bc238cdfb6995b3a2106dc`.

**Interprétation de l'identité système :** `/etc/os-release` peut continuer d'afficher Bazzite, car LEOS est construit sur cette base et conserve ses métadonnées de version. Ce seul fichier ne permet pas de conclure que l'installation est Bazzite au lieu de LEOS. Vérifier la source de déploiement dans `rpm-ostree status` et rechercher `ghcr.io/jovanille43/leos`.

Cette validation confirme l'installation complète et l'accès au premier bureau KDE dans la VM. Elle ne valide pas encore les transitions Desktop/Gaming, le réseau, l'audio, les services après plusieurs redémarrages, les périphériques physiques ni les performances de jeux. Les commits ultérieurs de `main` ne sont pas inclus dans l'ISO utilisée pour ce test tant qu'une nouvelle image et une nouvelle ISO n'ont pas été générées.

## État de la livraison courante — 27 novembre 2026

Le commit `dc1faf711670e558ae456ef02cc6f5bcf606c976` inclut la PR #73. Les contrôles Python ([run #45982477898](https://github.com/jovanille43/LEOS/actions/runs/45982477898)) et BlueBuild/QML ([run #45982478002](https://github.com/jovanille43/LEOS/actions/runs/45982478002)) sont réussis. La construction et la publication des trois images (AMD/Intel, NVIDIA legacy, NVIDIA modern) sont réussies ([run #45982477894](https://github.com/jovanille43/LEOS/actions/runs/45982477894)). La génération des trois ISO a été déclenchée automatiquement ([run #45983444147](https://github.com/jovanille43/LEOS/actions/runs/45983444147)) ; elle était encore en file d'attente lors de la rédaction de cet état.

Le dernier jeu d'ISO entièrement vérifié reste celui du commit précédent `dcd89660fdc45e6d77a030bd01426208459eaafc` ([run #45855325068](https://github.com/jovanille43/LEOS/actions/runs/45855325068)). Ne pas utiliser ces anciennes ISO pour valider les changements de la PR #73. Dès que le run #45983444147 est terminé, choisir l'artefact standard correspondant exactement à `dc1faf7`, vérifier les fichiers de checksum, digest source et manifeste, puis effectuer l'installation interactive dans la VM dédiée décrite ci-dessous.

## Objectif et limites

Cette étape sert à vérifier que l'ISO démarre, que l'installation aboutit sur un disque virtuel et que les premiers écrans LEOS sont utilisables. Elle ne certifie pas les pilotes GPU, le Wi-Fi, le Bluetooth, la veille, les manettes ni les performances d'un PC physique.

**Règle de sécurité :** ne jamais connecter un disque physique de l'ordinateur hôte à la VM. Toute installation doit viser uniquement le disque virtuel créé pour cette machine virtuelle.

## 1. Préparer et vérifier l'ISO

1. Ouvrir l'[historique du workflow ISO](https://github.com/jovanille43/LEOS/actions/workflows/iso.yml) et choisir la dernière exécution réussie déclenchée par un **push sur `main`** ou un lancement manuel (`workflow_dispatch`), pas une exécution `pull_request`. Vérifier que les étapes **Validate ISO boot structure, checksum, and source digest**, **Boot installer ISO with UEFI firmware in QEMU** et **Upload installer ISO and checksum** ont réussi. Les exécutions de pull request ignorent volontairement l'envoi de l'artefact ; ne pas télécharger l'ISO d'une telle exécution.
2. Extraire le ZIP dans un dossier dédié.
3. Vérifier que l'ISO et son fichier `.sha256` sont présents.
4. Depuis ce dossier, exécuter :

```bash
sha256sum --check LEOS-standard-latest.iso.sha256
```

Le résultat attendu est `LEOS-standard-latest.iso: OK`. En cas d'échec, ne pas démarrer l'ISO : extraire à nouveau l'archive ou la télécharger de nouveau.

Conserver également le fichier `LEOS-standard-latest.iso.source-digest`. Il indique le digest de l'image conteneur utilisé pour générer l'ISO. La validation confirme le checksum, le digest source, l'entrée UEFI, les principaux fichiers Anaconda et l'apparition de l'écran d'accueil Anaconda WebUI dans QEMU (notamment « Welcome. Let's install Fedora Linux now » et les étapes « Installation method » / « Storage configuration »). Elle ne réalise pas une installation complète sur disque virtuel, ne valide pas encore les étapes suivantes du parcours Anaconda et ne certifie pas la fin de l'installation.

## 2. Créer la machine virtuelle

Avec Virtual Machine Manager (`virt-manager`) et QEMU/KVM :

- Nom : `LEOS-VM-test`.
- Mémoire : 8 Gio si l'hôte en dispose suffisamment ; sinon 4 à 6 Gio pour un premier test d'interface.
- Processeurs : 4 vCPU si disponibles ; sinon 2 pour le premier démarrage.
- Disque : nouveau disque virtuel QCOW2 de 80 Gio, avec allocation dynamique.
- Firmware : UEFI (OVMF), pas BIOS Legacy.
- Réseau : NAT par défaut.
- Affichage : SPICE / Virtio, avec accélération 3D facultative.
- Audio : périphérique audio virtuel si proposé.

Attacher `LEOS-standard-latest.iso` comme CD/DVD virtuel et placer le lecteur CD/DVD en premier dans l'ordre de démarrage.

Ne pas activer le passthrough d'un disque physique, d'un contrôleur SATA/NVMe ou d'une partition de l'hôte. Ne pas sélectionner l'option d'installation sur le PC hôte.

### Si GNOME Boxes affiche « No KVM »

Ce message concerne la virtualisation disponible sur l'ordinateur hôte. Il ne signifie pas que l'ISO LEOS a échoué. GNOME Boxes et `virt-manager` utilisent normalement KVM pour accélérer QEMU ; changer simplement d'application ne corrige donc pas une absence de KVM.

Fermer le message d'erreur, puis lancer ces commandes de diagnostic dans un terminal Ubuntu :

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo
ls -l /dev/kvm
id -nG
lsmod | grep -E '^kvm'
```

Interprétation :

- Si la première commande renvoie `0`, redémarrer l'ordinateur dans les paramètres UEFI/BIOS et activer la virtualisation du processeur : **Intel Virtualization Technology (VT-x)** sur Intel ou **SVM Mode / AMD-V** sur AMD. Enregistrer, redémarrer Ubuntu et refaire les contrôles.
- Si le premier résultat est supérieur à `0`, mais que `/dev/kvm` est absent, vérifier que le module KVM correspondant au processeur est chargé. Sur Intel, essayer `sudo modprobe kvm_intel` ; sur AMD, essayer `sudo modprobe kvm_amd`. Ne lancer que la commande correspondant au processeur, puis vérifier à nouveau `ls -l /dev/kvm`.
- Si `/dev/kvm` existe mais que le compte n'a pas les droits d'accès, ajouter le compte au groupe KVM avec `sudo usermod -aG kvm "$USER"`, fermer complètement la session Ubuntu puis se reconnecter. Vérifier ensuite que `kvm` apparaît dans le résultat de `id -nG`.

Ne pas appliquer de `chmod` permissif à `/dev/kvm` et ne pas modifier les disques de l'hôte. Si le message persiste, conserver les résultats des quatre commandes pour identifier précisément le blocage.

Le pipeline CI de LEOS utilise aussi QEMU en émulation logicielle **TCG**, sans KVM. Un démarrage local via TCG est donc une solution de repli possible, mais il sera nettement plus lent que KVM ; le guide principal ci-dessous privilégie KVM pour l'installation interactive.

## 3. Démarrer et installer dans la VM

1. Démarrer la VM sur l'ISO.
2. Vérifier que l'environnement d'installation se charge, que l'interface Anaconda WebUI apparaît et que l'affichage reste utilisable. Attendre jusqu'à 5 minutes au premier démarrage ; si une erreur critique ou une boucle apparaît, arrêter le test et conserver les journaux au lieu de relancer une installation.
3. Vérifier que la connexion réseau NAT est détectée et que l'installateur propose une page de création du compte utilisateur. Le profil Server concerne uniquement l'environnement Anaconda ; l'image déployée reste LEOS. Créer le compte dans l'installateur. Si la page de création du compte est absente, annuler le test et consigner l'anomalie plutôt que poursuivre vers un système sans compte. Avant de confirmer le partitionnement, vérifier que le seul disque proposé est le disque virtuel QCOW2 de 80 Gio créé pour `LEOS-VM-test`.
4. Si le réseau est absent, si un disque réel de l'ordinateur hôte apparaît ou si le disque cible n'est pas clairement identifiable, annuler et arrêter l'installation.
5. Une fois le disque virtuel confirmé, effectuer l'installation dans la VM.
6. Redémarrer sur le disque virtuel installé et retirer/détacher l'ISO si nécessaire pour éviter de relancer l'installateur.

L'opération peut effacer le disque virtuel de cette VM ; elle ne doit jamais avoir accès au disque physique de l'hôte.

## 4. Contrôles après le premier démarrage

Cocher uniquement les tests réellement effectués :

- [x] Un compte utilisateur a été créé pendant l'installation Anaconda.
- [x] La connexion KDE fonctionne avec ce compte et son mot de passe.
- [x] L'installation se termine sans erreur.
- [x] Le système redémarre depuis le disque virtuel.
- [x] L'écran de connexion KDE apparaît.
- [x] La session KDE Desktop s'ouvre et reste utilisable.
- [ ] Le logo Desktop affiche le lion seul.
- [ ] Le sélecteur LEOS s'ouvre.
- [ ] Le guide de premier démarrage apparaît et peut être refermé.
- [ ] Desktop Mode et Gaming Mode peuvent être sélectionnés.
- [ ] Chaque transition demande une confirmation.
- [ ] Une application ouverte dans Desktop reste ouverte après un aller-retour de mode.
- [ ] Le retour de Gaming vers Desktop fonctionne.
- [ ] Les animations et sons se lisent correctement, ou leur désactivation permet une transition sans blocage.
- [ ] Le réseau NAT fournit une connexion.
- [ ] Le son via le périphérique audio virtuel fonctionne.
- [ ] Le système redémarre une seconde fois sans erreur.
- [ ] `systemctl --failed` ne signale aucun service essentiel en échec.

Dans cette base Bazzite immuable, il est normal que `cat /etc/os-release` conserve le nom Bazzite. Pour confirmer le système effectivement déployé, la ligne `ostree-image-signed:docker://ghcr.io/jovanille43/leos:latest` de `rpm-ostree status` est le contrôle déterminant.

Pour les contrôles système, ouvrir un terminal dans la VM et lancer :

```bash
rpm-ostree status
uname -r
cat /etc/os-release
systemctl --failed
systemctl --user --failed
```

## 5. Ce que la VM ne permet pas de certifier

Les points suivants restent réservés aux essais physiques :

- pilote et accélération réels AMD, Intel ou NVIDIA ;
- températures, VRAM et télémétrie GPU ;
- Wi-Fi et Bluetooth matériels ;
- veille, réveil et consommation d'un portable ;
- manettes USB/Bluetooth et reconnexion ;
- écrans externes, fréquences et configurations multi-écrans ;
- performances de jeux et compatibilité Vulkan de la carte réelle.

La carte graphique virtuelle de QEMU n'est pas une preuve de fonctionnement d'un pilote GPU physique. Ne pas utiliser le résultat VM pour annoncer une compatibilité NVIDIA, AMD ou Intel certifiée.

## 6. Compte rendu à conserver

Noter la date, le digest contenu dans le fichier `.source-digest`, les paramètres VM et le résultat de chaque contrôle. Pour chaque anomalie, conserver le message exact et les journaux utiles ; expurger les noms de compte, chemins personnels, adresses IP publiques et toute donnée privée avant de les partager.

Après une validation VM réussie, poursuivre avec la [checklist de validation sur machine réelle](hardware-validation.md) sur un PC ou un disque de test, sans toucher au poste principal.
