# Récupération et retour arrière LEOS

## Principe

LEOS repose sur Bazzite et son système de déploiements OSTree. La récupération d'une mise à jour défectueuse doit d'abord utiliser le déploiement précédent fourni par le système. LEOS ne doit pas inventer un second mécanisme de mise à jour, modifier les partitions automatiquement ou supprimer l'ancien déploiement.

Cette procédure concerne les images LEOS basées sur Bazzite avec OSTree. Les intitulés exacts du menu de démarrage peuvent varier selon la version de Bazzite et le firmware.

## Sauvegarder et restaurer les préférences LEOS

Le Centre de contrôle propose une page **Sauvegardes** dédiée aux réglages propres à LEOS. Elle permet de créer une copie privée des préférences connues : couleurs A/B, dernier mode utilisé, animations, sons, notifications et autres valeurs enregistrées par LEOS.

Les fichiers sont conservés dans `$XDG_STATE_HOME/leos/settings-backups/` (par défaut `~/.local/state/leos/settings-backups/`). Chaque sauvegarde comprend un fichier de données et un manifeste d'intégrité SHA-256. Le dossier et les fichiers sont créés avec des permissions privées ; les liens symboliques, fichiers non réguliers, données incomplètes et sauvegardes altérées sont refusés. LEOS conserve au maximum 20 sauvegardes vérifiées et supprime les plus anciennes après la création réussie d'une nouvelle copie.

La création d'une sauvegarde est refusée si un fichier de préférences existant est illisible ou trop volumineux : LEOS ne doit pas transformer ses valeurs de repli en copie présentée comme fidèle. Lors d'une restauration explicitement confirmée, un fichier corrompu mais de taille prise en charge est d'abord conservé à l'identique dans un fichier privé `corrupt-settings-<identifiant>.bin`, accompagné d'un manifeste `.meta` contenant sa taille et son SHA-256. Si ce fichier est trop volumineux ou ne peut pas être lu en sécurité, la restauration est refusée et le fichier actuel reste inchangé.

Pour restaurer :

1. Ouvrir le Centre de contrôle puis **Sauvegardes**.
2. Vérifier la liste des sauvegardes disponibles et sélectionner la date souhaitée ; la plus récente est présélectionnée.
3. Lire la confirmation : seule la configuration LEOS est remplacée.
4. Confirmer l'action. LEOS crée automatiquement une sauvegarde de l'état courant avant d'appliquer la copie vérifiée.

Pour exporter une copie hors du PC, sélectionner la sauvegarde voulue puis choisir **Exporter la sélection**. Choisir un dossier sur un support externe monté. LEOS y copie ensemble le fichier `.bak` et son manifeste `.json`, sans écraser des fichiers existants. Conserver les deux fichiers ayant le même identifiant : le manifeste permet de contrôler l'intégrité de la copie avant restauration.

Pour importer une copie externe, choisir **Importer depuis un support** puis sélectionner le manifeste `.json` ; le fichier `.bak` correspondant doit rester dans le même dossier. LEOS vérifie l'identifiant, la version du format, les valeurs de préférences et le SHA-256 avant l'import. Une sauvegarde déjà présente ou altérée est refusée sans remplacer les fichiers locaux.

La restauration remplace uniquement `$XDG_CONFIG_HOME/leos/settings.json` (par défaut `~/.config/leos/settings.json`). Elle ne modifie ni les données personnelles, ni les comptes, ni les jeux, ni les applications, ni les panneaux ou fichiers de configuration KDE. Les préférences de disposition dans `desktop-layout.json` et la configuration de Plasma ne sont pas incluses dans cette sauvegarde ; elles disposent de mécanismes distincts. La validation des valeurs est rejouée avant écriture ; une sauvegarde invalide n'est jamais appliquée. Une restauration explicitement confirmée peut également remplacer un fichier de préférences LEOS devenu illisible.

**Important :** la sauvegarde automatique reste locale au disque et ne protège pas contre la panne ou la perte de ce disque. Utilise l'export vers un support distinct pour conserver une copie externe. Ces snapshots ne remplacent pas une sauvegarde des documents et données personnelles.

## Sauvegarder et restaurer les dispositions du bureau LEOS

Le Centre de contrôle propose un bloc indépendant **Sauvegarde des dispositions LEOS** dans les réglages du bureau. Il protège uniquement les préférences propres à LEOS enregistrées dans `$XDG_CONFIG_HOME/leos/desktop-layout.json` (par défaut `~/.config/leos/desktop-layout.json`) : profil choisi, activation et position du dock, alignement, masquage automatique et activation des widgets.

Les points de restauration sont conservés dans `$XDG_STATE_HOME/leos/desktop-layout-backups/` (par défaut `~/.local/state/leos/desktop-layout-backups/`). Chaque sauvegarde comprend un fichier `.bak` et un manifeste `.json` avec identifiant, version du format, taille et empreinte SHA-256. Le dossier est privé, les fichiers sont limités à 0600 et LEOS conserve au maximum 20 sauvegardes vérifiées. Les données invalides, les liens symboliques, les fichiers non réguliers et les paires dont l'empreinte ne correspond pas sont refusés.

Pour créer une sauvegarde, utiliser **Créer une sauvegarde**. Pour déplacer une copie vers un support USB, sélectionner une entrée puis **Exporter** ; les deux fichiers sont copiés ensemble, sans écraser de fichier déjà présent. Pour importer, choisir **Importer** et sélectionner le manifeste `.json`, en conservant le fichier `.bak` correspondant dans le même dossier. L'identifiant, le schéma, les valeurs et l'empreinte sont revérifiés avant l'import.

La restauration demande une confirmation explicite et crée automatiquement une sauvegarde de l'état actuel avant de remplacer les préférences. Si le fichier courant est corrompu, trop volumineux, illisible ou lié symboliquement, LEOS refuse la restauration et le laisse intact plutôt que de risquer de perdre son contenu. La copie restaurée ne modifie pas directement les panneaux ou applets KDE.

**Périmètre séparé :** ces copies ne comprennent ni les paramètres généraux `settings.json`, ni la configuration réelle des panneaux et applets Plasma (`plasma-org.kde.plasma.desktop-appletsrc`), ni les fichiers personnels. Les préférences générales et la configuration Plasma gardent leurs propres mécanismes de sauvegarde. Une sauvegarde locale ne protège pas contre la perte du disque : exporter vers un support physique distinct reste nécessaire.

## Avant une mise à jour

1. Sauvegarder les fichiers personnels importants sur un autre support.
2. Vérifier que le système démarre normalement et que le réseau fonctionne.
3. Dans un terminal, consulter l'état des déploiements :

   ```bash
   rpm-ostree status
   ```

4. Vérifier qu'un déploiement précédent est encore disponible dans la liste. Ne pas lancer de nettoyage manuel des anciens déploiements avant d'avoir validé la mise à jour.
5. Effectuer la mise à jour par le mécanisme natif Bazzite/OSTree et redémarrer lorsque le système le demande.

Pour une mise à jour à risque, il est possible de préserver un déploiement connu comme fonctionnel avec le mécanisme de pinning OSTree. Consulte d'abord `rpm-ostree status -v`, identifie précisément l'index du déploiement, puis utilise `sudo ostree admin pin <index>`. **Ne réutilise jamais un ancien index sans relire l'état** : les index peuvent changer après une transaction. Cette protection conserve un déploiement système, pas les données personnelles.

Les fichiers personnels du répertoire utilisateur ne sont normalement pas remplacés par un changement de déploiement OSTree. Cela ne remplace pas une sauvegarde : les partitions de données, les applications Flatpak et les données de configuration doivent être sauvegardées selon leur emplacement et leur importance.

## Lecture des déploiements dans le Centre de contrôle

La page **Mises à jour** peut afficher un inventaire local issu de `rpm-ostree status --json` : version du déploiement démarré, préfixe de son checksum, nombre d'autres entrées conservées, entrées préparées et entrées épinglées. Cette lecture est effectuée périodiquement tant que le Centre de contrôle est ouvert.

Cet inventaire ne certifie pas que chaque ancienne entrée peut démarrer ou servir de retour arrière. Il ne remplace pas la lecture complète de `rpm-ostree status`. LEOS ne lance aucune commande de rollback, de pinning ou de nettoyage depuis cette page ; toute intervention reste volontaire et doit suivre la procédure ci-dessous.

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

## Référence Bazzite

La procédure suit le guide officiel [Bazzite — Rollbacks](https://docs.bazzite.gg/Installing_and_Managing_Software/Updates_Rollbacks_and_Rebasing/rolling_back_system_updates/), qui décrit le choix du déploiement de secours dans GRUB, le retour arrière depuis une session démarrée et le pinning des déploiements. Les intitulés du menu et les options disponibles peuvent varier selon l'image et la version.
