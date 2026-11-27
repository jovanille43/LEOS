# Programme de finition LEOS

Ce document fixe les huit axes de finition validés pour LEOS. Il distingue les fonctions présentes dans les sources, celles qui restent à intégrer et les validations qui doivent encore être réalisées sur une installation réelle. Un test automatisé réussi ne vaut pas certification matérielle.

## État au 27 novembre 2026

La branche `main` est au commit `29ac036683f444296a97daebea3f8eb398c5a6f8` (PR #75 fusionnée). Les contrôles Python ont exécuté 1 169 tests (1 ignoré, aucun échec) ; les contrôles BlueBuild ont réussi. Le build des trois images AMD/Intel, NVIDIA legacy et NVIDIA moderne est réussi dans le run [#45988546222](https://github.com/jovanille43/LEOS/actions/runs/45988546222). La génération ISO est déclenchée par le succès de ce build ; les trois artefacts correspondant à `29ac036` ne sont pas encore validés dans ce document. Le dernier lot ISO complet disponible comme preuve reste le run #45855325068 sur `dcd8966`, antérieur à la finition graphique #75. L'installation interactive en VM et le contrôle visuel réel de Plasma restent à effectuer sur le commit courant.

## Ordre de travail

### 1. Installation et première expérience

- [x] Exiger le choix des couleurs A/B avant l'accès aux modes.
- [x] Présenter le profil Desktop LEOS avec sauvegarde et retour arrière.
- [x] Vérifier que le sélecteur, son QML et les ressources de bureau sont présents dans l'image publiée.
- [x] Mettre le choix d'activation du profil LEOS au premier plan pour le clavier et la manette.
- [ ] Valider l'ensemble du parcours après une installation complète de l'ISO courante dans une VM : création de compte, ouverture de session, identité A/B, activation Desktop, Gaming et retour Desktop.
- [x] Afficher l'état du premier démarrage en trois étapes (identité A/B, guide de bienvenue, profil Desktop appliqué ou volontairement ignoré) dans le sélecteur LEOS ; la vérification après installation reste à faire.

### 2. Identité visuelle cohérente

- [x] Unifier la direction graphite/métal et les accents A/B ; conserver des surfaces neutres et ne jamais imposer de combinaison d'accents.
- [x] Prévoir les modes sombre, clair et automatique.
- [x] Séparer visuellement les états système (critique, attention, normal) des accents de marque A/B.
- [x] Ajouter un contrat de cohérence A/B partagé entre les interfaces LEOS.
- [ ] Contrôler chaque écran et chaque état (vide, chargement, erreur, sélection, focus) sur plusieurs résolutions.
- [ ] Valider le thème réellement appliqué dans Plasma, et pas uniquement les composants QML.

### 3. Gaming plug-and-play

- [x] Bibliothèque unifiée et navigation clavier/manette : Steam, Heroic, Lutris, playlists RetroArch et ajout manuel.
- [x] Détection en lecture seule des sept émulateurs, profils de manettes et assistant de configuration Eden (clés/firmware locaux, prérequis et ouverture de l'émulateur installé).
- [x] Imports et commandes de lancement depuis les dossiers choisis par l'utilisateur pour Dolphin, PCSX2, PPSSPP, melonDS, Eden et RPCS3 ; aucune recherche globale de ROM.
- [x] Import des playlists RetroArch avec le cœur indiqué par l'entrée ou le cœur par défaut de la playlist lorsqu'il est disponible.
- [x] Ajouter les indications de configuration guidée pour Eden, PCSX2, melonDS et RPCS3, ainsi que l'aide au choix des cœurs RetroArch sans installer implicitement des fichiers système ou des contenus protégés.
- [ ] Valider installations et lancements réels sur Bazzite, notamment Eden et RPCS3, ainsi que stockage externe, veille/reprise, écrans multiples et GPU hybrides.

### 4. Centre de contrôle intelligent

- [x] Inventaires matériel, réseau, stockage et télémétrie disponible.
- [x] Diagnostic système et rapports de support expurgés.
- [x] Ajouter un résumé de santé système à la vue d'ensemble, avec accès direct au diagnostic détaillé.
- [x] Présenter l'état du déploiement OSTree, les risques et les conséquences des actions de récupération ; afficher une pré-vérification avant d'ouvrir le gestionnaire natif de mises à jour Bazzite.

### 5. Boutique LEOS

- [x] Catalogue, filtres, sources et confirmation explicite.
- [x] Contrôles de compatibilité et respect du modèle immuable de Bazzite.
- [x] Alimenter les catégories directement depuis le catalogue validé, afficher le nombre de résultats filtrés et proposer un état vide récupérable.
- [x] Étendre la recherche aux informations de compatibilité et aux notes d'opération.
- [x] Ajouter des recommandations issues du catalogue réellement installable et des mises à jour Flatpak ciblées avec vérification de l'origine Flathub, double contrôle avant opération et confirmation explicite.
- [ ] Tester sur Bazzite réel l'installation et la mise à jour ciblées, les dépendances/runtime, l'annulation, les échecs réseau et la désinstallation.

### 6. Sécurité, sauvegarde et récupération

- [x] Appui sur les déploiements OSTree/Bazzite et documentation du rollback.
- [x] Inventaire en lecture seule du déploiement démarré, des autres entrées, des préparations et des entrées épinglées ; aucune suppression ni transaction automatique.
- [x] Sauvegarde avant modification du profil Plasma.
- [x] Transformer l'inventaire en guide de récupération contextualisé selon le déploiement démarré ; expliquer les options sûres, les prérequis et les conséquences avant de renvoyer vers les outils natifs.
- [ ] Tester réellement la mise à jour, le redémarrage, le choix d'un ancien déploiement, le rollback et la conservation des données dans une VM.

### 7. Expérience Desktop complète

- [x] Menu, dock, notifications et accès aux paramètres KDE.
- [x] Ajouter les accès directs depuis le menu Desktop au gestionnaire de fichiers et aux paramètres KDE, avec retour visible si l'application est absente.
- [ ] Finaliser les flux de recherche universelle, espaces de travail et multi-écrans.
- [ ] Vérifier les applications quotidiennes, le lancement automatique et la reprise de session.

### 8. Validation et livraison

- [x] CI Python, lint QML, contrôles BlueBuild et vérification de signature.
- [x] Génération des trois variantes ISO avec vérification de structure, checksum, digest source, manifeste de provenance et démarrage UEFI/QEMU jusqu'à Anaconda WebUI (commit `dcd8966`, run #45855325068).
- [x] Reconstruire, publier et signer les trois images après la finition graphique #75 (`29ac036`) — build [#45988546222](https://github.com/jovanille43/LEOS/actions/runs/45988546222), AMD/Intel, NVIDIA legacy et NVIDIA moderne réussis.
- [ ] Générer et vérifier les trois ISO de `29ac036` après le build #45988546222 ; vérifier structure, checksum, digest, provenance et démarrage UEFI/QEMU, puis réaliser une installation interactive.
- [x] Ajouter un manifeste de provenance par ISO : variante, commit source, tag et digest d'image, SHA-256 et périmètre exact du test UEFI/QEMU.
- [ ] Répéter ces contrôles sur le commit exact de livraison et conserver les artefacts correspondants.
- [ ] Installer l'ISO du commit de livraison dans une VM UEFI dédiée et documenter les résultats : création de compte, session, identité A/B, profil Desktop, Gaming, transitions, réseau/audio, second démarrage.
- [ ] Tester les trois variantes graphiques sur du matériel adapté avant d'annoncer une compatibilité certifiée.

## Règle de livraison

Une fonction n'est considérée comme terminée que lorsque son implémentation, ses tests automatisés, son intégration dans l'image et sa validation d'exécution sont distingués clairement. Aucun écran conceptuel ni build de conteneur ne doit être présenté comme une capture réelle ou une ISO validée.
