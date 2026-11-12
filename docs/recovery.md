# Récupération et retour arrière LEOS

## Principe

LEOS repose sur Bazzite et son système de déploiements OSTree. La récupération d'une mise à jour défectueuse doit d'abord utiliser le déploiement précédent fourni par le système. LEOS ne doit pas inventer un second mécanisme de mise à jour, modifier les partitions automatiquement ou supprimer l'ancien déploiement.

Cette procédure concerne les images LEOS basées sur Bazzite avec OSTree. Les intitulés exacts du menu de démarrage peuvent varier selon la version de Bazzite et le firmware.

## Avant une mise à jour

1. Sauvegarder les fichiers personnels importants sur un autre support.
2. Vérifier que le système démarre normalement et que le réseau fonctionne.
3. Dans un terminal, consulter l'état des déploiements :

   ```bash
   rpm-ostree status
   ```

4. Vérifier qu'un déploiement précédent est encore disponible dans la liste. Ne pas lancer de nettoyage manuel des anciens déploiements avant d'avoir validé la mise à jour.
5. Effectuer la mise à jour par le mécanisme natif Bazzite/OSTree et redémarrer lorsque le système le demande.

Les fichiers personnels du répertoire utilisateur ne sont normalement pas remplacés par un changement de déploiement OSTree. Cela ne remplace pas une sauvegarde : les partitions de données, les applications Flatpak et les données de configuration doivent être sauvegardées selon leur emplacement et leur importance.

## Si le nouveau déploiement ne démarre pas

1. Redémarrer le PC.
2. Ouvrir le menu de démarrage du chargeur et choisir le déploiement précédent de Bazzite/OSTree, s'il est proposé.
3. Une fois la session précédente démarrée, ouvrir un terminal et examiner l'état :

   ```bash
   rpm-ostree status
   systemctl --failed
   ```

4. Si le système précédent est fonctionnel et que le déploiement courant doit être abandonné, demander le retour arrière natif :

   ```bash
   sudo rpm-ostree rollback
   systemctl reboot
   ```

5. Après le redémarrage, vérifier que le système fonctionne et contrôler à nouveau :

   ```bash
   rpm-ostree status
   systemctl --failed
   systemctl --user --failed
   ```

La commande de rollback modifie le déploiement par défaut ; elle ne répare pas un disque endommagé, un chargeur de démarrage absent ou une panne matérielle. Ne pas la lancer à l'aveugle si la sortie de `rpm-ostree status` ne montre pas clairement les déploiements disponibles.

## Si aucun déploiement ne démarre

1. Ne pas formater le disque et ne pas relancer une installation par-dessus les données existantes.
2. Démarrer depuis un support Bazzite/Fedora de secours compatible UEFI.
3. Si les données sont importantes, privilégier leur copie vers un support externe avant toute tentative de réparation.
4. Conserver les journaux et relever la version de l'image, le noyau, le GPU et le message d'erreur.
5. Réinstaller uniquement après avoir identifié le disque cible, compris les conséquences du partitionnement et vérifié la sauvegarde.

Un support live peut aider à diagnostiquer ou copier des données ; il ne garantit pas une réparation automatique d'un déploiement OSTree ou du chargeur de démarrage. Toute réparation manuelle doit être documentée et adaptée à la sortie réelle des outils.

## Diagnostic à collecter

Depuis le système démarré, lorsque cela est possible :

```bash
rpm-ostree status
uname -r
cat /etc/os-release
systemctl --failed
journalctl -b -p warning
journalctl -b -p err
```

Avant de partager les journaux, masquer les noms d'utilisateur, chemins personnels, adresses IP publiques, noms de machines et identifiants.

## Règles de sécurité LEOS

- Aucun rollback, nettoyage ou repartitionnement automatique par LEOS.
- Aucun effacement de données ou réinstallation silencieuse.
- L'utilisateur doit voir clairement le déploiement actif et le déploiement de secours disponible.
- La procédure doit être testée sur une machine dédiée avant toute publication.
- La présence d'un ancien déploiement ne doit jamais être présentée comme une sauvegarde complète.
- Si le système ne peut pas confirmer une information, il doit l'indiquer plutôt que supposer que la récupération est possible.

## Validation avant diffusion

Sur chaque variante matérielle LEOS, tester sur un PC de test :

- [ ] état initial des déploiements consigné ;
- [ ] mise à jour vers une image de test ;
- [ ] démarrage normal du nouveau déploiement ;
- [ ] sélection du précédent déploiement depuis le menu de démarrage ;
- [ ] exécution de `rpm-ostree rollback` et redémarrage ;
- [ ] confirmation du déploiement actif après retour arrière ;
- [ ] vérification des données utilisateur, Flatpak et paramètres ;
- [ ] démarrage depuis un support live UEFI et copie de données vers un disque externe.

Tant que ces essais physiques ne sont pas terminés, la récupération est documentée mais **non certifiée sur matériel réel**.
