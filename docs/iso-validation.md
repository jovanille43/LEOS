# Validation de l’ISO LEOS et du support USB

## Objectif et état

Ce guide sépare quatre contrôles qui ne prouvent pas la même chose :

1. l’intégrité du fichier ISO téléchargé ;
2. l’authenticité de l’ISO et de son manifeste ;
3. l’écriture fidèle de l’image sur la clé USB ;
4. le vrai démarrage et l’installation dans un environnement de test.

Au 17 novembre 2026, l’ISO standard e33a010-45 a été générée et signée par GitHub Actions (run 43946765765). Le workflow vérifie sa somme SHA-256 et sa signature. Le contrôle statique du catalogue UEFI est ajouté au pipeline. En revanche, aucun démarrage complet ni aucune installation réussie dans une machine virtuelle ou sur du matériel réel ne sont encore enregistrés. Le premier essai physique a échoué au contrôle média ; une autre tentative a échoué pendant « Installation des logiciels ». La cause reste à diagnostiquer.

## Risque connu dans la chaîne de génération

Le workflow actuel appelle \`bluebuild generate-iso\`. La documentation officielle de BlueBuild indique que cette commande utilise \`JasonN3/build-container-installer\` sous le capot. Or le dépôt amont a été archivé le 26 octobre 2026 ; son mainteneur a annoncé sa fin de vie le 27 septembre 2026, notamment parce que le passage de Lorax à Kiwi demanderait une réécriture. La chaîne actuelle doit donc être considérée comme **transitoire**, et non comme une dépendance durable pour les futures ISO.

Cela ne signifie pas que ce composant est la cause de l’échec LEOS. Il existe toutefois des signalements d’échecs Anaconda pendant le déploiement d’images OSTree où le message générique masque l’erreur réelle dans \`/tmp/packaging.log\`. Une erreur connue mentionne \`Pathname can't be converted from UTF-8 to current locale\` ; des rapports amont relient ce symptôme à des chemins de fichiers non ASCII présents dans les couches d’une image. Ce sont des pistes de diagnostic, pas un diagnostic confirmé de LEOS.

En cas d’échec à « Installation des logiciels » :
1. récupérer \`/tmp/packaging.log\` avant de refaire l’installation ;
2. chercher le message OSTree réel, notamment les erreurs de locale ou de conversion de chemin ;
3. si un chemin non ASCII est mentionné, examiner les fichiers de l’image et de ses couches parentes, pas seulement les fichiers ajoutés par les modules LEOS ;
4. conserver le journal expurgé dans le dossier de diagnostic du ticket, sans publier d’informations personnelles.

Références amont :
- [Guide BlueBuild de génération ISO](https://blue-build.org/how-to/generate-iso/) — précise le recours à \`build-container-installer\`.
- [Fin de vie de build-container-installer, issue #215](https://github.com/JasonN3/build-container-installer/issues/215) — dépôt archivé et mainteneur ayant annoncé l’arrêt.
- [Erreur d’installation OSTree / Unicode, BlueBuild issue #310](https://github.com/blue-build/cli/issues/310).
- [Erreur générique de déploiement Anaconda, build-container-installer issue #150](https://github.com/JasonN3/build-container-installer/issues/150).

### Chaîne candidate Titanoboa

Une implémentation séparée existe maintenant sur `feature/titanoboa-installer`, dans `.github/workflows/iso-titanoboa.yml`. Elle reprend la méthode Live de Bazzite : image Live KDE basée sur Bazzite, image LEOS explicitement embarquée dans le stockage Podman, puis génération par Titanoboa. L'action Titanoboa est épinglée sur le commit `5c457c3d0518bd17e754be0fd98a60d29d26abb4`.

Le déclenchement manuel du workflow ISO ne sera disponible dans GitHub Actions qu'après que le fichier soit présent sur la branche par défaut ; la PR de migration est pour le moment un brouillon non fusionné.

Cette intégration est une candidate, pas une validation. Les trois nouvelles images LEOS doivent d'abord être reconstruites sur cette branche pour contenir la politique Sigstore et la clé publique. Ensuite seulement le workflow ISO peut être lancé. La première étape à valider est une installation complète sur une VM UEFI avec disque vierge ; aucun test matériel ni dual boot n'est enregistré. Voir [le détail du flux et ses critères de validation](titanoboa-installer.md).

Référence amont : [ublue-os/titanoboa](https://github.com/ublue-os/titanoboa).

## 1. Vérifier le fichier téléchargé

Télécharge l’ISO, son fichier .sha256, son manifeste JSON de provenance et les deux bundles .sigstore.json depuis le même artefact GitHub Actions. Extrais tous les fichiers dans un même dossier.

Vérifie la somme :

~~~bash
sha256sum --check LEOS-standard-e33a010-45.iso.sha256
~~~

Vérifie ensuite les signatures avec cosign.pub, la clé publique présente à la racine du dépôt :

~~~bash
cosign verify-blob --key cosign.pub --bundle LEOS-standard-e33a010-45.iso.sigstore.json LEOS-standard-e33a010-45.iso
cosign verify-blob --key cosign.pub --bundle LEOS-standard-e33a010-45.iso.json.sigstore.json LEOS-standard-e33a010-45.iso.json
~~~

Utilise les noms de fichiers exacts de l’artefact. Si un contrôle échoue, arrête-toi : ne grave pas l’ISO et ne tente pas de l’installer. La clé privée de signature reste exclusivement dans le secret GitHub Actions ; elle ne doit jamais être exportée ou partagée.

## 2. Vérification statique de l’ISO par la CI

Après sa génération, le workflow exécute .github/scripts/verify-installer-iso.sh. Ce script :

- refuse une ISO vide ou sans fichier SHA-256 associé ;
- revérifie l’empreinte du fichier ;
- inspecte le catalogue El Torito avec xorriso ;
- échoue si aucune entrée d’amorçage UEFI n’est annoncée.

Ce contrôle protège contre une ISO mal formée ou un catalogue UEFI absent. Il ne lance pas de firmware, ne démarre pas Anaconda et ne réalise pas une installation. La validation QEMU/UEFI et les tests physiques restent des étapes séparées.

## 3. Vérifier l’écriture de la clé USB

Identifie le support avec lsblk. Vérifie le modèle et la capacité ; le périphérique choisi doit être la clé USB entière, pas une partition et surtout pas le SSD interne. L’écriture brute efface les données du support.

Après l’écriture et la synchronisation, une comparaison en lecture seule peut détecter une écriture incomplète. Depuis le dossier de l’ISO :

~~~bash
ISO=LEOS-standard-e33a010-45.iso
DEVICE=/dev/sdX
ISO_SIZE=$(stat -c '%s' "$ISO")
sha256sum "$ISO"
sudo head -c "$ISO_SIZE" "$DEVICE" | sha256sum
~~~

Remplace /dev/sdX par le nom vérifié du disque USB entier. Les deux empreintes doivent être identiques. La commande lit les premiers octets du périphérique et ne les modifie pas. Si elles diffèrent, réécris le support ou utilise une autre clé et/ou un autre port.

## 4. Démarrer l’installateur

Démarre explicitement en mode UEFI. Sur le menu LEOS, l’option « Test this media & install LEOS » exécute le contrôle du support avant l’installateur. Un résultat FAIL est un arrêt obligatoire : ne passe pas outre pour installer. Même si l’ISO téléchargée a une empreinte correcte, le support USB peut avoir été mal écrit ou être défectueux.

L’ISO actuelle ouvre l’installateur Fedora/Anaconda ; elle n’offre pas de session de bureau Live dans le parcours actuellement observé.

## 5. Installation de validation en machine virtuelle

La validation suivante doit être effectuée sur une VM x86_64 avec firmware UEFI et un disque virtuel jetable :
- démarrage du support et passage du contrôle média ;
- affichage du menu de démarrage et ouverture de l’interface Anaconda ;
- installation sur un disque virtuel vierge de taille suffisante ;
- fin de l’installation sans erreur, retrait de l’ISO virtuelle et démarrage du système installé ;
- vérification de KDE, du réseau, du GPU virtuel et de l’état OSTree.

Le succès de cette VM ne remplace pas les essais sur PC physique, mais permet de détecter un échec générique de l’installateur sans risquer les partitions d’un ordinateur personnel.

## 6. Validation distincte du dual boot

Le dual boot doit être testé séparément dans une VM jetable contenant déjà un système UEFI/GPT et un espace non alloué. Il faut confirmer :
- que le système existant reste amorçable ;
- que la partition EFI existante n’est pas formatée ;
- que seules les zones de disque explicitement sélectionnées sont modifiées ;
- que LEOS démarre depuis son entrée de démarrage ;
- que le système préexistant démarre toujours après l’installation.

Aucun test de dual boot ne doit être fait sur le seul PC principal tant que cette checklist n’est pas passée sur une VM puis sur une machine de test avec sauvegarde.

## 7. Critères avant publication

Une ISO ne peut être proposée au téléchargement public qu’après :
- somme SHA-256 et signatures valides ;
- catalogue UEFI validé dans la CI ;
- contrôle média réussi sur le support utilisé ;
- installation et premier démarrage réussis sur une VM UEFI ;
- installation et premier démarrage réussis sur au moins une machine physique adaptée ;
- notes de version, variante GPU, limites connues et procédure de récupération publiées.

La compatibilité générale ou le dual boot ne doivent jamais être promis à partir d’un seul test.
