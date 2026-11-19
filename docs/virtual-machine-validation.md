# Première validation LEOS en machine virtuelle

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

## 3. Démarrer et installer dans la VM

1. Démarrer la VM sur l'ISO.
2. Vérifier que l'environnement d'installation se charge, que l'interface Anaconda WebUI apparaît et que l'affichage reste utilisable. Attendre jusqu'à 5 minutes au premier démarrage ; si une erreur critique ou une boucle apparaît, arrêter le test et conserver les journaux au lieu de relancer une installation.
3. Vérifier que la connexion réseau NAT est détectée. Avant de confirmer le partitionnement, vérifier que le seul disque proposé est le disque virtuel QCOW2 de 80 Gio créé pour `LEOS-VM-test`.
4. Si le réseau est absent, si un disque réel de l'ordinateur hôte apparaît ou si le disque cible n'est pas clairement identifiable, annuler et arrêter l'installation.
5. Une fois le disque virtuel confirmé, effectuer l'installation dans la VM.
6. Redémarrer sur le disque virtuel installé et retirer/détacher l'ISO si nécessaire pour éviter de relancer l'installateur.

L'opération peut effacer le disque virtuel de cette VM ; elle ne doit jamais avoir accès au disque physique de l'hôte.

## 4. Contrôles après le premier démarrage

Cocher uniquement les tests réellement effectués :

- [ ] L'installation se termine sans erreur.
- [ ] Le système redémarre depuis le disque virtuel.
- [ ] L'écran de connexion KDE apparaît.
- [ ] La session KDE Desktop s'ouvre et reste utilisable.
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
