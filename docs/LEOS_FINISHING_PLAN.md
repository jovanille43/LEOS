# Programme de finition LEOS

Ce document fixe les huit axes de finition validés pour LEOS. Il distingue les fonctions présentes dans les sources, celles qui restent à intégrer et les validations qui doivent encore être réalisées sur une installation réelle. Un test automatisé réussi ne vaut pas certification matérielle.

## Ordre de travail

### 1. Installation et première expérience

- [x] Exiger le choix des couleurs A/B avant l'accès aux modes.
- [x] Présenter le profil Desktop LEOS avec sauvegarde et retour arrière.
- [x] Vérifier que le sélecteur, son QML et les ressources de bureau sont présents dans l'image publiée.
- [x] Mettre le choix d'activation du profil LEOS au premier plan pour le clavier et la manette.
- [ ] Valider l'ensemble du parcours après une installation complète de l'ISO courante dans une VM : création de compte, ouverture de session, identité A/B, activation Desktop, Gaming et retour Desktop.
- [ ] Ajouter une vue d'état du premier démarrage qui indique les étapes terminées et celles laissées volontairement de côté.

### 2. Identité visuelle cohérente

- [x] Unifier la direction graphite/métal et les accents A/B.
- [x] Prévoir les modes sombre, clair et automatique.
- [ ] Contrôler chaque écran et chaque état (vide, chargement, erreur, sélection, focus) sur plusieurs résolutions.
- [ ] Valider le thème réellement appliqué dans Plasma, et pas uniquement les composants QML.

### 3. Gaming plug-and-play

- [x] Bibliothèque unifiée et navigation clavier/manette.
- [x] Détection des émulateurs et gestion des profils de contrôleurs.
- [ ] Compléter les imports, la détection des jeux et les parcours de lancement par plateforme.
- [ ] Terminer l'intégration Eden pour Switch avec transparence sur les prérequis, les sources et la compatibilité.
- [ ] Tester les scénarios de manette, veille/reprise, écrans multiples et GPU hybrides sur matériel réel.

### 4. Centre de contrôle intelligent

- [x] Inventaires matériel, réseau, stockage et télémétrie disponible.
- [x] Diagnostic système et rapports de support expurgés.
- [ ] Regrouper l'état matériel dans une vue de santé lisible, sans inventer de capteurs.
- [ ] Clarifier les actions recommandées, les risques et les redémarrages nécessaires avant confirmation.

### 5. Boutique LEOS

- [x] Catalogue, filtres, sources et confirmation explicite.
- [x] Contrôles de compatibilité et respect du modèle immuable de Bazzite.
- [ ] Améliorer la découverte par catégories et recommandations réellement installables.
- [ ] Tester les cas de mise à jour, dépendances, annulation, échec réseau et désinstallation.

### 6. Sécurité, sauvegarde et récupération

- [x] Appui sur les déploiements OSTree/Bazzite et documentation du rollback.
- [x] Sauvegarde avant modification du profil Plasma.
- [ ] Ajouter un état de récupération compréhensible depuis le Centre de contrôle.
- [ ] Tester réellement mise à jour, ancien déploiement, rollback et conservation des données.

### 7. Expérience Desktop complète

- [x] Menu, dock, notifications et accès aux paramètres KDE.
- [ ] Finaliser les flux explorateur, recherche, espaces de travail et multi-écrans.
- [ ] Vérifier les applications quotidiennes, le lancement automatique et la reprise de session.

### 8. Validation et livraison

- [x] CI Python, lint QML, contrôles BlueBuild et vérification de signature.
- [x] Génération ISO avec vérification de structure, checksum et démarrage UEFI/QEMU.
- [ ] Répéter ces contrôles sur le commit exact de livraison et conserver les artefacts correspondants.
- [ ] Installer cette ISO dans une VM et documenter les captures/résultats du parcours post-installation.
- [ ] Tester les trois variantes graphiques sur du matériel adapté avant d'annoncer une compatibilité certifiée.

## Règle de livraison

Une fonction n'est considérée comme terminée que lorsque son implémentation, ses tests automatisés, son intégration dans l'image et sa validation d'exécution sont distingués clairement. Aucun écran conceptuel ni build de conteneur ne doit être présenté comme une capture réelle ou une ISO validée.
