# Architecture LEOS

## 1. Principe général

LEOS est une seule installation basée sur Bazzite KDE Desktop. Desktop Mode et Gaming Mode sont deux expériences utilisateur complémentaires qui partagent le même système.

## 2. Composants

- **Bazzite KDE** : système de base, pilotes, services et mécanismes de mise à jour/rollback.
- **Desktop Mode** : KDE Plasma personnalisé, sans remplacer les fonctions natives utiles.
- **Gaming Mode** : application LEOS plein écran lancée au-dessus de KDE ; KDE reste actif en arrière-plan.
- **LEOS Control Center** : accès simplifié aux fonctions spécifiques LEOS et aux outils Linux avancés.
- **LEOS Store** : catalogue unifié s'appuyant sur les sources et gestionnaires existants.

## 3. Technologies

- **Qt 6 / QML** pour l'interface Gaming et ses animations.
- **PySide6** pour la logique applicative et les intégrations Python de la première version.
- Des services et outils Linux existants pour les fonctions système ; ne pas réimplémenter les mécanismes déjà fournis par Bazzite/KDE.

Le choix d'une couche C++ dédiée pourra être réévalué si un composant nécessite des performances ou une intégration que PySide6 ne fournit pas suffisamment.

## 4. Bibliothèque Gaming

La bibliothèque unifie les catalogues locaux exposés par les lanceurs intégrés, sans remplacer ces lanceurs.

- Imports automatiques actuellement présents : manifestes Steam, Heroic (Epic/Legendary, GOG et Amazon Games) et Lutris.
- Ajout manuel de jeux avec commande d'arguments séparés ; aucun shell n'est utilisé.
- Jaquettes lues uniquement dans les caches locaux Steam/Lutris ou les chemins d'images locaux référencés par les manifestes Heroic. Aucune image distante n'est téléchargée.
- Catégories de navigation : PC Gaming, Nintendo, PlayStation, SEGA, Arcade, Favoris et Récemment joués. Les catégories console/arcade sont des emplacements de navigation, pas la preuve d'une intégration d'émulateur.
- Fiche de jeu : titre, plateforme, source, identifiant de catalogue, état des fichiers locaux et jaquette disponible. Les chemins privés et arguments de lancement ne sont pas exposés à QML.
- Les titres sont harmonisés sans réécrire leur présentation ; la recherche ignore casse et accents. Les correspondances exactes sont signalées comme doublons potentiels sans fusion ni suppression.
- Les imports sont isolés par fournisseur : une erreur d'accès à un catalogue ou à une jaquette ne bloque pas les autres fournisseurs.
- Les jeux dont les fichiers sont absents peuvent rester affichés pour les disques externes déconnectés ; l'état est présenté comme absent ou inconnu plutôt que supposé installé.

Les introductions vidéo des transitions Desktop/Gaming sont raccordées à Qt Multimedia, avec pistes audio intégrées et comportement de repli. Les animations propres aux jeux, les fiches cinématiques, les métadonnées en ligne, l'import d'émulateurs/consoles et les jaquettes distantes ne sont pas encore intégrés. Les capacités de détection et de lancement dépendent de chaque lanceur et format ; aucune compatibilité universelle n'est revendiquée.

## 5. Contrôles et performances

- Panneau rapide horizontal en haut de l'interface Gaming.
- Inventaire CPU/RAM et télémétrie GPU/VRAM/température lorsqu'elles sont exposées par les interfaces DRM/hwmon du pilote.
- Les valeurs indisponibles restent absentes ; aucun capteur ni FPS n'est simulé.
- L'overlay FPS s'appuie sur MangoHud uniquement lorsqu'il est installé et activé. Il n'existe pas encore de compteur FPS interne LEOS.
- Les profils d'énergie sont ceux réellement proposés par `power-profiles-daemon` ; LEOS ne pilote pas directement les ventilateurs.
- Les données matérielles et profils nécessitent une validation sur les matériels ciblés ; les capacités varient selon pilotes et services présents.

## 6. Boutique et opérations sensibles

La boutique s'appuie sur Flatpak/Flathub, les mécanismes natifs Bazzite et les intégrations de lanceurs compatibles.

Avant toute installation ou désinstallation, présenter :
- les éléments concernés ;
- la source ;
- la compatibilité connue ;
- les dépendances et effets attendus.

Demander une confirmation explicite avant l'opération. Ne pas contourner l'architecture immuable de Bazzite.

## 7. Démarrage et transitions entre modes

- Après l'ouverture de la session KDE, le sélecteur LEOS s'affiche à chaque démarrage de session.
- Il présente l'heure, la date, le dernier mode utilisé et deux grandes cartes Desktop/Gaming.
- Desktop ferme uniquement le sélecteur et laisse apparaître le bureau KDE déjà actif ; Gaming lance l'application LEOS plein écran au-dessus de la même session.
- Le dernier mode choisi est mémorisé et présenté au prochain démarrage, sans imposer de lancement automatique.
- L'entrée vers Gaming demande une confirmation ; le retour vers Desktop demande également une confirmation depuis Gaming.
- Aucune application ouverte n'est terminée automatiquement. Les applications KDE restent en arrière-plan pendant Gaming, sous réserve de leur propre comportement.
- Le sélecteur ne remplace pas SDDM : il apparaît après l'authentification de l'utilisateur.
- Il accepte la souris, le clavier et les manettes reconnues via evdev en lecture seule ; il réutilise les profils contrôleur LEOS sans modifier globalement les entrées Linux.
- Les raccourcis globaux KDE pour passer directement d'un mode à l'autre restent à intégrer et à valider.

## 8. Compatibilité matérielle

LEOS ne doit pas dépendre d'un seul modèle de processeur ou de carte graphique. La cible initiale suit la base Bazzite : x86_64 et démarrage UEFI. La référence Gaming publiée par Bazzite inclut 8 Go de RAM, un processeur quadricœur à 2 GHz, un GPU Vulkan 1.3+ et 50 Go libres sur SSD interne (120 Go recommandés).

La recette actuelle utilise l'image Bazzite générale. Une seconde variante basée sur l'image Bazzite NVIDIA doit être ajoutée avant d'annoncer la prise en charge complète des GPU NVIDIA. Les PC hybrides et les périphériques radio/audio doivent être testés sur matériel réel. Les sondes LEOS restent en lecture seule et affichent les capacités absentes comme indisponibles.

Le Centre de contrôle expose un précontrôle indicatif x86_64 / UEFI / RAM. Ce contrôle partiel ne certifie pas la compatibilité GPU/Vulkan, CPU, Wi-Fi, Bluetooth ou périphériques. La politique et la matrice de tests sont détaillées dans [hardware-compatibility.md](hardware-compatibility.md).

## 9. Principes de développement

1. Construire d'abord une version minimale fonctionnelle.
2. Préserver la stabilité et les mécanismes natifs de Bazzite.
3. Séparer interface, logique applicative et intégrations système.
4. Documenter les fonctions prévues et distinguer clairement celles réellement implémentées.
5. Tester sur plusieurs matériels avant de déclarer une fonction compatible.
