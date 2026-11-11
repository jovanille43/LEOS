# LEOS 🦁

**LEOS** est une distribution Linux personnalisée basée sur **Bazzite KDE**. Son objectif est de réunir une expérience de bureau élégante et un environnement gaming immersif au sein d'un seul système.

> **État du projet :** prototype en développement. Le dépôt contient des premières applications sources (Gaming, sélecteur de modes, Centre de contrôle, Centre des manettes et boutique), mais elles ne sont pas encore validées sur une session Bazzite réelle ni intégrées dans une ISO installable.

## Vision

LEOS propose deux expériences au sein d'une seule installation :

- **Desktop Mode** — bureau KDE personnalisé, avec l'emblème LEOS représentant le lion seul.
- **Gaming Mode** — application LEOS plein écran au-dessus de KDE, pensée pour la manette, avec l'emblème du lion tenant une manette.

Les deux modes partagent le même système, les mêmes fichiers, applications, pilotes et services. Le passage d'un mode à l'autre se fait sans redémarrage. Avant une transition, LEOS demande quoi faire des applications ouvertes.

## Identité visuelle

L'identité LEOS repose sur un lion métallique, des éclairages cyan et magenta, une typographie dédiée et un fond noir.

- Desktop : emblème officiel du lion seul.
- Gaming : emblème officiel du lion avec manette.
- Les animations et sons LEOS seront configurables et désactivables.

Les références visuelles fournies pour le projet doivent être respectées. L'image comparative des deux emblèmes sert de référence et ne doit pas devenir le visuel principal d'un écran.

## Base technique

| Élément | Choix |
| --- | --- |
| Système de base | Bazzite KDE Desktop |
| Construction de l'image | BlueBuild |
| Interface Gaming | Qt 6 / QML avec logique applicative PySide6 |
| Interface Desktop | KDE Plasma personnalisé |
| Gestion des manettes | Linux evdev via python3-evdev |
| Dépôt | GitHub |
| Distribution visée | Image LEOS dédiée, puis ISO installable |

LEOS conserve les mécanismes natifs de Bazzite, KDE et Linux. Les composants spécifiques au projet complètent cette base sans créer de gestionnaires concurrents ni contourner le modèle immuable de Bazzite.

### Premiers composants présents dans le dépôt

- Backend Gaming PySide6 : détection initiale des jeux Steam via les manifestes locaux et ajout manuel de jeux.
- Tableau technique : premières mesures CPU/RAM et température CPU lorsque les capteurs sont exposés ; GPU et FPS restent à intégrer.
- Préférences communes : enregistrement local du dernier mode et des options LEOS dans le profil utilisateur.
- Sélecteur de modes Desktop/Gaming, restauration du dernier mode et entrée de menu KDE préparés.
- Premier Centre de contrôle LEOS : préférences de thème, animations, sons, overlay et profil de performances enregistrées localement.
- Centre des manettes : détection des contrôleurs Linux, test des entrées, profils locaux, zone morte et enregistrement du neutre des sticks.
- Première boutique LEOS : catalogue initial, recherche, catégories, détection des Flatpak installés et opérations soumises à confirmation explicite.
- Vérifications automatiques du code Python et tests du stockage local via GitHub Actions.

Ces éléments sont des prototypes source. Leur intégration dans Bazzite, leurs dépendances QML, les raccourcis globaux, les contrôles manette et les transitions réelles restent à tester et compléter.

## Gaming Mode

- Application LEOS plein écran au-dessus de KDE ; KDE reste actif en arrière-plan.
- Interface utilisable à la manette, au clavier et à la souris.
- Bibliothèque unifiée de jeux PC et de jeux émulés.
- Détection automatique des jeux installés et ajout manuel.
- Métadonnées et jaquettes récupérées automatiquement lorsque disponibles, avec édition manuelle.
- Fiches de jeux cinématiques et transition animée à chaque lancement ; option de désactivation.
- Retour à la bibliothèque avec une animation discrète après fermeture d'un jeu.
- Panneau rapide horizontal en haut de l'écran.
- Tableau de bord technique complet accessible depuis ce panneau.
- Overlay de performances en jeu discret, facultatif et personnalisable.
- Intégration des lanceurs et émulateurs compatibles, sans les remplacer.
- Quelques émulateurs essentiels préinstallés ; les autres proposés dans la boutique.

## Desktop Mode

- Bureau KDE personnalisé avec l'identité LEOS.
- Menu principal LEOS et dock personnalisable avec dispositions prédéfinies.
- Centre de contrôle simplifié pour les fonctions propres à LEOS, avec accès aux paramètres Linux avancés.
- Thèmes, fonds d'écran, sons et animations configurables.

## Centre des manettes

Le Centre des manettes propose une vue des contrôleurs détectés par Linux, un test des boutons et axes analogiques, des profils locaux par appareil, le réglage d'une zone morte et l'enregistrement de la position neutre des axes.

Les préférences sont enregistrées dans le compte Linux de l'utilisateur. Le prototype ne modifie pas les mappings du système ou des jeux : les configurations Steam et des lanceurs restent prioritaires jusqu'à la mise en place de leurs intégrations LEOS.

## Boutique LEOS

La boutique proposera jeux, émulateurs, applications, utilitaires et éléments de personnalisation. Elle s'appuiera sur Flatpak/Flathub, les mécanismes natifs de Bazzite et les intégrations de lanceurs compatibles.

**Toute installation ou désinstallation exige une confirmation explicite.** Chaque fiche doit préciser le contenu de l'opération, sa source, sa compatibilité et ses éventuelles dépendances.

## Principes de sécurité et de fiabilité

- Aucune installation ou désinstallation sans confirmation.
- Aucune fermeture d'application sans choix explicite de l'utilisateur lors d'une transition.
- Les mises à jour utilisent les mécanismes natifs de Bazzite ; l'utilisateur décide de leur installation.
- Les opérations de nettoyage, suppression ou modification système demandent une confirmation.
- Les limites de compatibilité matérielle et logicielle sont indiquées clairement.

## Structure du dépôt

```text
LEOS/
├── .github/workflows/   # Automatisation et vérifications
├── branding/            # Logos, animations, sons et ressources
├── config/              # Configuration partagée de LEOS
├── controller_center/   # Gestion et test des manettes
├── control_center/      # Paramètres LEOS
├── desktop/             # Personnalisation du Desktop Mode
├── docs/                # Architecture et documentation
├── gaming/              # Application Gaming LEOS
├── shop/                # Boutique LEOS et opérations Flatpak confirmées
├── recipe.yml           # Recette BlueBuild
└── README.md
```

## Feuille de route

1. **Fondations** — structurer le dépôt et valider la recette BlueBuild.
2. **Image minimale** — construire et tester une première image LEOS basée sur Bazzite.
3. **Identité LEOS** — intégrer les premiers éléments visuels et le sélecteur de mode.
4. **Desktop Mode** — développer progressivement le bureau personnalisé.
5. **Gaming Mode** — développer l'application plein écran et la bibliothèque.
6. **Intégrations** — boutique, paramètres et outils LEOS.
7. **Tests et ISO** — vérifier la compatibilité, la stabilité et préparer une image installable.

## État actuel

- [x] Dépôt GitHub créé.
- [x] Première recette BlueBuild ajoutée (squelette à valider).
- [x] Premier workflow GitHub Actions ajouté (provisoire, à valider).
- [x] Architecture générale des deux modes définie.
- [x] Premiers prototypes Gaming, Centre de contrôle, Boutique et Centre des manettes ajoutés au dépôt.
- [ ] Valider la recette et le workflow avant compilation.
- [ ] Configurer la clé de signature dans les secrets GitHub.
- [ ] Construire et tester la première image LEOS.

**Aucune image LEOS compilée ni ISO installable n'est encore disponible.** Le workflow de validation Python est en place ; ses résultats devront être consultés sur GitHub Actions.

---

*LEOS — One system. Two experiences.*
