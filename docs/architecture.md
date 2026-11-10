# Architecture LEOS

## 1. Principe général

LEOS est une seule installation basée sur Bazzite KDE Desktop. Desktop Mode et Gaming Mode sont deux expériences utilisateur complémentaires qui partagent le même système.

## 2. Composants

- **Bazzite KDE** : système de base, pilotes, services et mécanismes de mise à jour/rollback.
- **Desktop Mode** : KDE Plasma personnalisé, sans remplacer les fonctions natives utiles.
- **Gaming Mode** : application plein écran LEOS lancée au-dessus de KDE ; KDE reste actif en arrière-plan.
- **LEOS Control Center** : accès simplifié aux fonctions spécifiques LEOS et aux outils Linux avancés.
- **LEOS Store** : catalogue unifié s'appuyant sur les sources et gestionnaires existants.

## 3. Technologies

- **Qt 6 / QML** pour l'interface Gaming et ses animations.
- **PySide6** pour la logique applicative et les intégrations Python de la première version.
- Des services et outils Linux existants pour les fonctions système ; ne pas réimplémenter les mécanismes déjà fournis par Bazzite/KDE.

Le choix d'une couche C++ dédiée pourra être réévalué si un composant nécessite des performances ou une intégration que PySide6 ne fournit pas suffisamment.

## 4. Bibliothèque Gaming

La bibliothèque centralise les entrées provenant des lanceurs PC et des émulateurs compatibles.

- Détection automatique lorsque les lanceurs exposent les informations nécessaires.
- Ajout manuel pour les jeux non détectés.
- Jaquettes et métadonnées récupérées depuis des sources disponibles ; édition manuelle possible.
- Catégories prévues : PC Gaming, Nintendo, PlayStation, SEGA, Arcade, Favoris et Récemment joués.
- Les fiches sont cinématiques ; une transition est jouée à chaque lancement et peut être désactivée.
- À la fermeture d'un jeu, retour à la bibliothèque avec une animation discrète.

Les capacités de détection et de lancement dépendent de chaque lanceur, émulateur et format de jeu. Ne jamais présenter une intégration comme universelle sans l'avoir testée.

## 5. Contrôles et performances

- Panneau rapide horizontal en haut de l'interface Gaming.
- Tableau de bord technique complet accessible depuis ce panneau.
- Overlay de performances en jeu discret, facultatif et personnalisable.
- Affichage des seules données réellement disponibles : FPS, températures, charge CPU/GPU, mémoire et autres capteurs compatibles.

## 6. Boutique et opérations sensibles

La boutique s'appuie sur Flatpak/Flathub, les mécanismes natifs Bazzite et les intégrations de lanceurs compatibles.

Avant toute installation ou désinstallation, présenter :
- les éléments concernés ;
- la source ;
- la compatibilité connue ;
- les dépendances et effets attendus.

Demander une confirmation explicite avant l'opération. Ne pas contourner l'architecture immuable de Bazzite.

## 7. Transitions entre modes

- Accès par bouton et raccourcis clavier.
- Raccourcis prévus : Super + G pour Gaming, Super + D pour Desktop, plus un raccourci personnalisable pour ouvrir le sélecteur.
- Le dernier mode utilisé est mémorisé pour le démarrage.
- Avant une transition, demander à l'utilisateur s'il souhaite conserver les applications en arrière-plan ou fermer proprement la session concernée.
- La conservation effective des applications dépendra de l'architecture des processus et devra être testée ; ne pas promettre une conservation parfaite.

## 8. Principes de développement

1. Construire d'abord une version minimale fonctionnelle.
2. Préserver la stabilité et les mécanismes natifs de Bazzite.
3. Séparer interface, logique applicative et intégrations système.
4. Documenter les fonctions prévues et distinguer clairement celles réellement implémentées.
5. Tester sur plusieurs matériels avant de déclarer une fonction compatible.
