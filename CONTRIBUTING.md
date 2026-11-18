# Contribuer à LEOS

Merci de contribuer à LEOS. Le projet est une distribution basée sur Bazzite KDE ; les changements doivent préserver les mécanismes natifs de Bazzite, KDE, OSTree et Linux.

## Avant de commencer

- Lire [l'architecture](docs/architecture.md), la [compatibilité matérielle](docs/hardware-compatibility.md) et le [processus de publication](docs/release-process.md).
- Vérifier les Pull Requests ouvertes pour éviter les changements en doublon.
- Les travaux incomplets doivent rester en brouillon et déclarer clairement leurs dépendances.
- Une PR ne doit pas changer de secrets, embarquer de clé privée ou afficher des données sensibles.

## Règles de développement

- Détecter les capacités disponibles à l'exécution ; ne jamais inventer de mesures matérielles.
- Préserver le mode Desktop lorsque les fonctions Gaming optionnelles sont indisponibles.
- Ne fermer, supprimer ou fusionner aucune donnée utilisateur sans confirmation explicite dans l'interface LEOS.
- Utiliser des arguments de processus explicites ; éviter le shell pour lancer des applications ou opérations système.
- Toute installation, désinstallation, suppression ou modification sensible doit présenter un aperçu et demander une confirmation.
- Épingler les actions GitHub sur un SHA et vérifier les images de build par digest.
- Ne jamais committer `cosign.key`, les fichiers `.env` contenant des secrets ou les identifiants de compte.

## Vérifications avant PR

Depuis la racine du dépôt :

```bash
python -m compileall -q gaming launcher control_center controller_center shop leos_core desktop tests
python -m unittest discover -s tests -v
```

Pour les changements QML, exécuter également le lint Qt Quick utilisé dans `.github/workflows/recipe-checks.yml`. Pour les recettes, ressources de marque, workflows ou scripts de packaging, exécuter les contrôles BlueBuild correspondants.

Toute modification d'installation ou de session doit préciser :
- le comportement attendu ;
- les risques pour le système ou les données ;
- le chemin de retour arrière ;
- les variantes matérielles concernées ;
- les essais en VM ou sur matériel réel nécessaires.

## Pull Requests

- Une PR doit être ciblée, expliquer le besoin et décrire les fichiers sensibles touchés.
- Indiquer les tests exécutés et leur résultat réel.
- Déclarer explicitement les validations non réalisées.
- Les modifications de marque doivent préciser la provenance et les droits des ressources.
- Les changements qui touchent aux images, signatures, installation, stockage ou démarrage nécessitent une revue dédiée.
- Les changements expérimentaux ne doivent pas être fusionnés dans `main` avant la réussite des contrôles et la revue des impacts.

La configuration GitHub doit imposer une Pull Request et les contrôles Python/BlueBuild avant toute fusion dans `main`. Voir [l'entretien du dépôt](docs/github-maintenance.md).
