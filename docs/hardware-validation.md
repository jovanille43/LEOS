# LEOS — Checklist de validation sur machine réelle

Cette checklist est destinée au premier démarrage d'une image LEOS sur un **PC de test**. Elle complète les tests Python et la validation BlueBuild ; elle ne doit pas être considérée comme exécutée tant que les contrôles n'ont pas été réalisés sur le matériel.

## Matrice de compatibilité à couvrir

La cible est la famille des PC modernes compatibles avec Bazzite, pas un assemblage matériel unique. Réaliser les validations sur plusieurs familles avant d'annoncer une compatibilité générale :

| Famille | Configuration à tester | Point de vigilance |
| --- | --- | --- |
| Intel intégré | iGPU Intel récent | Accélération, vidéo, multi-écran |
| AMD intégré | APU Ryzen avec Radeon intégrée | Accélération, veille et sorties vidéo |
| AMD dédié | Radeon RX | Pilote, VRAM, jeux et télémétrie |
| NVIDIA dédié | GeForce avec image/variante Bazzite adaptée | Pilote propriétaire, Secure Boot selon configuration |
| Portable hybride | iGPU + GPU dédié | Sélection GPU, consommation, veille |
| PC bureautique | GPU intégré, RAM et stockage modestes mais conformes aux prérequis Bazzite | Desktop fluide, absence de GPU dédié |
| Multi-écran | Résolutions et fréquences différentes | Mise à l'échelle, orientation et réveil |
| Périphériques | Wi-Fi, Bluetooth, audio USB/Bluetooth, manettes USB/Bluetooth | Détection et reconnexion |

Ne pas transformer ce tableau en liste de matériels minimaux imposés. Les prérequis d'installation et de pilotes restent ceux de la version Bazzite utilisée. Le projet doit détecter les fonctions indisponibles et préserver un mode Desktop utilisable.

## 1. Préparer un environnement sûr

- [ ] Utiliser un PC de test ou un disque de test, pas l'installation principale.
- [ ] Préparer un support de récupération Bazzite connu comme fonctionnel.
- [ ] Vérifier que les données importantes du PC de test sont sauvegardées.
- [ ] Noter le modèle du GPU, le type de contrôleur, l'écran et les périphériques audio.
- [ ] Vérifier la présence de la clé publique Cosign et du secret Actions avant de lancer la construction signée.
- [ ] Construire et publier l'image LEOS ; relever son tag et son digest.

Ne pas modifier les partitions du PC principal pour cette première validation. Conserver un moyen de revenir à un déploiement Bazzite fonctionnel.

## 2. Contrôles système après le premier démarrage

Dans un terminal :

```bash
rpm-ostree status
uname -r
cat /etc/os-release
systemctl --failed
systemctl --user --failed
```

- [ ] Le système démarre sans boucle de démarrage.
- [ ] La session KDE s'ouvre et reste utilisable.
- [ ] Le réseau filaire ou Wi-Fi fonctionne.
- [ ] Le son fonctionne sur au moins une sortie PipeWire.
- [ ] Le GPU et le pilote attendus sont détectés.
- [ ] Aucun service essentiel n'est en échec.
- [ ] Le sélecteur LEOS s'ouvre après l'ouverture de session KDE.

En cas d'anomalie, collecter les journaux avant toute modification :

```bash
journalctl -b -p warning
journalctl --user -b -p warning
rpm-ostree status --json
```

Masquer les noms d'utilisateur, chemins personnels, adresses IP publiques et identifiants avant de partager des journaux.

## 3. Identité visuelle et introductions vidéo

- [ ] L'emblème Desktop affiche le lion seul.
- [ ] L'emblème Gaming affiche le lion avec la manette.
- [ ] Les images se chargent sans bloquer l'écran de sélection.
- [ ] L'entrée dans Desktop joue `desktop-intro.mov`.
- [ ] L'entrée dans Gaming joue `gaming-intro.mp4`.
- [ ] Le retour depuis Gaming joue l'introduction Desktop avant le retour au bureau.
- [ ] L'audio est audible sur la sortie sélectionnée et reste synchronisé avec la vidéo.
- [ ] Le réglage des sons coupe uniquement l'audio des introductions.
- [ ] Le réglage des animations désactive la vidéo et permet une transition immédiate.
- [ ] Une vidéo manquante ou illisible ne bloque pas le changement de mode.
- [ ] L'interface reste réactive pendant et après chaque transition.

Les vidéos actuellement hébergées ont passé le contrôle CI de présence des flux vidéo/audio et le décodage FFmpeg. Cela ne garantit pas à lui seul leur compatibilité avec le backend Qt Multimedia de la version Bazzite testée.

## 4. Transitions Desktop / Gaming

- [ ] La confirmation avant l'entrée dans Gaming est affichée.
- [ ] La confirmation avant le retour vers Desktop est affichée.
- [ ] Les applications ouvertes restent en arrière-plan.
- [ ] Aucune application n'est fermée automatiquement.
- [ ] Le dernier mode utilisé est mémorisé correctement.
- [ ] Un échec de lancement Gaming laisse une possibilité de retour au bureau.
- [ ] Le clavier, la souris et la manette permettent de naviguer dans le sélecteur.

## 5. Gaming Mode

- [ ] L'application s'ouvre en plein écran et reste au premier plan.
- [ ] La bibliothèque affiche les catégories prévues.
- [ ] Les jeux Steam installés sont importés correctement.
- [ ] Les jeux Heroic et Lutris sont importés lorsqu'ils sont présents.
- [ ] Les jeux manquants ou désinstallés sont signalés sans être supprimés automatiquement.
- [ ] Les favoris, jeux récents et recherches persistent après redémarrage.
- [ ] Les jaquettes locales s'affichent lorsqu'elles existent.
- [ ] Les jeux se lancent sans passer par un shell.
- [ ] Les erreurs de lancement sont compréhensibles.
- [ ] Les profils d'énergie n'affichent que les profils réellement disponibles.
- [ ] Les valeurs GPU indisponibles restent indiquées comme telles.
- [ ] Sur un PC hybride, toutes les cartes graphiques visibles sont identifiées sans confondre les connecteurs DRM avec des GPU supplémentaires.
- [ ] Deux GPU du même modèle mais avec des adresses PCI différentes apparaissent séparément dans l'inventaire ; plusieurs nœuds DRM d'une même carte ne créent pas de doublon.
- [ ] Sur un PC avec deux GPU NVIDIA, les mesures `nvidia-smi` sont associées à la bonne carte même si l'ordre de sortie diffère de l'ordre DRM.
- [ ] Sur un PC mixte Intel/AMD + NVIDIA, aucune mesure NVIDIA n'est attribuée à l'iGPU ou à un autre GPU dont l'identifiant PCI ne correspond pas.
- [ ] L'absence ou le délai d'expiration de `nvidia-smi` laisse Gaming Mode utilisable ; les mesures indisponibles sont signalées comme telles.
- [ ] La télémétrie Gaming sélectionne un GPU qui expose réellement ses mesures ; tester notamment iGPU + GPU dédié.
- [ ] Les températures CPU/GPU correspondent à des capteurs identifiés et ne sont pas remplacées par des estimations.
- [ ] MangoHud n'est proposé que lorsqu'il est installé.

## 6. Manettes et Bluetooth

- [ ] Une manette USB est détectée.
- [ ] Une manette Bluetooth est détectée après association.
- [ ] Les boutons, la croix directionnelle et les sticks sont reconnus.
- [ ] Les profils Xbox, PlayStation et Nintendo sont appliqués lorsque leur détection est fiable.
- [ ] Le retour/confirmation fonctionne avec la manette.
- [ ] Les contrôleurs continuent de fonctionner après un changement de mode.
- [ ] Le Bluetooth reste actif dans Desktop et Gaming.
- [ ] Un casque ou une enceinte Bluetooth peut être associé et utilisé comme sortie audio.

La pile BlueZ, PipeWire et les paramètres KDE restent ceux fournis par Bazzite ; ne pas ajouter de service Bluetooth concurrent pour corriger un problème avant d'avoir identifié sa cause.

## 7. Centre de contrôle et applications Desktop

- [ ] Le Centre de contrôle affiche CPU, estimation des cœurs physiques, mémoire, stockage, GPU et version Vulkan par GPU lorsque disponible, sans valeurs inventées.
- [ ] Le précontrôle Gaming distingue les seuils détectés des critères non vérifiables (fréquence CPU, type de SSD, compatibilité des pilotes) et ne bloque jamais Desktop Mode.
- [ ] Les interfaces réseau, le Wi-Fi et le Bluetooth sont détectés lorsque disponibles.
- [ ] Les diagnostics sont consultables sans modifier le système.
- [ ] Le nettoyage affiche un aperçu avant suppression.
- [ ] Toute suppression demande une confirmation explicite.
- [ ] Les mises à jour sont détectées sans être installées automatiquement par LEOS.
- [ ] Les notifications LEOS persistent et restent discrètes en Gaming.
- [ ] Les paramètres KDE avancés restent accessibles.
- [ ] Les préférences et sauvegardes Plasma ne sont pas appliquées sans accord explicite.

## 8. Apparence et fonds d'écran
## 8. Affichage et multi-écrans

- [ ] Un écran interne eDP et un écran HDMI/DisplayPort externe sont détectés lorsqu'ils sont exposés par DRM.
- [ ] La déconnexion et la reconnexion d'un écran mettent à jour l'inventaire sans faire planter le Centre de contrôle.
- [ ] Les connecteurs débranchés ne sont pas comptés comme des écrans connectés.
- [ ] Les modes annoncés par le pilote sont affichés sans être confondus avec le mode actuellement actif.
- [ ] Les configurations avec plusieurs écrans de résolutions et fréquences différentes restent gérées par KDE/KScreen.
- [ ] La mise à l'échelle, l'orientation, l'écran principal, le réveil après veille et les branchements à chaud sont vérifiés manuellement dans KDE.
- [ ] Une absence de connecteur DRM ou de modes exposés reste une information « non vérifiable » et ne bloque pas LEOS.
- [ ] LEOS n'applique jamais automatiquement une résolution, une fréquence, une orientation ou une disposition d'écran.


- [ ] Les aperçus Desktop et Gaming s'affichent dans la page Apparence du Centre de contrôle.
- [ ] Si un aperçu affiche son texte de repli, vérifier le chargement du plugin Qt SVG et la résolution du JPEG référencé depuis le SVG.
- [ ] Le bouton de sélection ouvre le module natif KDE `kcm_wallpaper`.
- [ ] Le sélecteur KDE permet de parcourir `/usr/share/leos/branding/wallpapers/`.
- [ ] Le fond Desktop affiche le lion seul, sans déformation ni recadrage involontaire.
- [ ] Le fond Gaming affiche le lion avec la manette, sans déformation ni recadrage involontaire.
- [ ] La résolution et la netteté sont correctes sur chaque écran connecté, y compris en multi-écrans.
- [ ] Annuler le sélecteur KDE ne modifie pas le fond actif.
- [ ] Aucun fond LEOS n'est appliqué automatiquement à la connexion ou au changement de mode.

Le Centre de contrôle ouvre uniquement le sélecteur natif ; l'utilisateur garde la décision finale et peut restaurer son fond précédent depuis KDE.

## 9. Boutique LEOS

Effectuer les essais avec une application Flatpak non critique.

- [ ] Le catalogue indique la source et la compatibilité.
- [ ] Les dépendances/runtime connus sont affichés.
- [ ] Une confirmation explicite précède chaque installation.
- [ ] Une confirmation explicite précède chaque désinstallation.
- [ ] L'inventaire distingue les installations utilisateur et système.
- [ ] Une désinstallation volontaire n'est pas annulée par le service d'installation initiale.
- [ ] Une opération refusée ou échouée laisse l'état cohérent.

## 10. Mises à jour, rollback et stabilité

Suivre également le [guide de récupération et de retour arrière](recovery.md). Les commandes OSTree doivent être testées uniquement sur une machine ou un disque de test, jamais sur le seul poste de travail.

- [ ] Vérifier l'état OSTree avant toute mise à jour.
- [ ] Effectuer une mise à jour uniquement après avoir confirmé que le déploiement de test peut être restauré.
- [ ] Redémarrer et vérifier que le nouveau déploiement démarre.
- [ ] Vérifier que les applications et les données utilisateur sont conservées.
- [ ] Tester le mécanisme natif de rollback sur le PC de test.
- [ ] Vérifier que le retour au déploiement précédent restaure un système fonctionnel.
- [ ] Laisser le système fonctionner plusieurs heures, puis vérifier les journaux et les services.

Ne pas tester un rollback ou une opération OSTree risquée sur le seul PC de travail.

## 11. Compte rendu

Pour chaque anomalie, consigner :

- modèle du PC et GPU ;
- version Bazzite de base et noyau ;
- mode concerné ;
- étapes précises pour reproduire ;
- résultat attendu et résultat obtenu ;
- extrait de journal expurgé des informations privées.

## Critères de validation

Une première image LEOS peut être considérée comme **validée sur cette machine** uniquement lorsque les sections 2 à 10 ont été exécutées, que les transitions vidéo/audio sont vérifiées dans Qt Multimedia, et qu'aucune régression bloquante n'est présente. La compatibilité d'une machine ne prouve pas celle de tous les GPU ou périphériques.
