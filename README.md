# LEOS 🦁

**LEOS** est un projet de distribution Linux personnalisée, construite à partir de **Bazzite KDE**. Son objectif est de réunir une expérience de bureau élégante et un environnement gaming immersif au sein d'un seul système.

> **État du projet :** phase de conception et de structuration. Les fonctionnalités décrites ci-dessous sont des objectifs, pas des fonctionnalités déjà intégrées.

## Vision

LEOS proposera deux environnements complémentaires :

- **Desktop Mode** — un bureau Linux soigné, personnalisable et adapté à l'utilisation quotidienne. Son identité visuelle utilise l'emblème LEOS avec le lion seul.
- **Gaming Mode** — une interface plein écran pensée pour la manette, organisée autour d'une bibliothèque de jeux et d'outils gaming. Son emblème représente le lion avec une manette.

L'utilisateur pourra passer d'un mode à l'autre à tout moment, avec un bouton ou un raccourci clavier. LEOS demandera quoi faire des applications ouvertes avant la transition.

## Identité visuelle

L'identité LEOS repose sur un lion métallique, des éclairages cyan et magenta, une typographie dédiée et un fond noir.

- Desktop : emblème du lion seul.
- Gaming : emblème du lion avec la manette.

Les animations et sons de transition seront personnalisables et pourront être désactivés.

## Base technique

| Élément | Choix |
| --- | --- |
| Système de base | Bazzite KDE Desktop |
| Construction de l'image | BlueBuild |
| Dépôt de développement | GitHub |
| Distribution visée | Image LEOS dédiée, puis ISO installable |

LEOS cherchera à conserver les fonctionnalités natives de Bazzite et de KDE plutôt que de recréer les outils Linux existants. Les composants spécifiques à LEOS viendront compléter cette base.

## Fonctionnalités envisagées

### Desktop Mode
- Bureau KDE personnalisé selon l'identité LEOS.
- Dock personnalisable et dispositions prédéfinies.
- Centre de contrôle LEOS pour les fonctions propres au projet.
- Thèmes, fonds d'écran et animations configurables.

### Gaming Mode
- Interface plein écran utilisable à la manette, au clavier et à la souris.
- Bibliothèque unifiée de jeux PC et de jeux émulés.
- Accès aux plateformes et outils compatibles avec Linux.
- Informations système et performances dans un tableau de bord discret.
- Gestion des manettes et profils de configuration.

### Fonctions communes
- Sélecteur de mode et raccourcis personnalisables.
- Notifications et identité sonore LEOS.
- Boutique envisagée pour les applications, jeux, émulateurs et thèmes.
- Assistant LEOS facultatif, avec des fonctions d'aide et de recommandation.
- Mises à jour proposées à l'utilisateur, qui garde le contrôle de leur installation.

La disponibilité et les performances de chaque fonction dépendront du matériel, des pilotes et de la compatibilité Linux.

## Architecture du dépôt

La structure sera enrichie progressivement. Les principaux éléments prévus sont :

- `recipe.yml` — recette BlueBuild de l'image LEOS.
- `.github/workflows/` — automatisation de la construction et des vérifications.
- `config/` — configuration propre à LEOS.
- `desktop/` — éléments du Desktop Mode.
- `gaming/` — éléments du Gaming Mode.
- `branding/` — logos, animations, sons et ressources visuelles.

Les dossiers seront ajoutés au fur et à mesure que leur contenu sera défini.

## Feuille de route

1. **Fondations** — structurer le dépôt et valider la recette BlueBuild.
2. **Première image** — construire une image LEOS minimale basée sur Bazzite.
3. **Identité LEOS** — intégrer les premiers éléments visuels et le sélecteur de mode.
4. **Desktop Mode** — développer progressivement le bureau personnalisé.
5. **Gaming Mode** — développer l'interface gaming et la bibliothèque.
6. **Tests et ISO** — vérifier la compatibilité, la stabilité et préparer une image installable.

## État actuel

- [x] Dépôt GitHub créé.
- [x] Première recette BlueBuild ajoutée.
- [x] Premier workflow GitHub Actions ajouté.
- [ ] Recette et workflow à valider avant toute compilation.
- [ ] Clé de signature à configurer dans les secrets GitHub.
- [ ] Première image LEOS à construire et tester.

**Aucune image LEOS compilée ni ISO installable n'est encore disponible.**

## Philosophie du projet

LEOS doit rester personnalisable, cohérent, fiable et simple à utiliser. Les actions sensibles — fermeture d'applications, nettoyage, suppression ou modification système — devront demander une confirmation à l'utilisateur.

---

*LEOS — One system. Two experiences.*
