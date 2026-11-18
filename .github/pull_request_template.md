## Objectif

<!-- Quel problème cette PR résout-elle ? -->

## Changements

<!-- Décrire les changements observables. -->

## Validation

- [ ] `python -m compileall -q gaming launcher control_center controller_center shop leos_core desktop tests`
- [ ] `python -m unittest discover -s tests -v`
- [ ] Lint QML si des fichiers QML sont modifiés
- [ ] Contrôles BlueBuild si recettes, workflows, ressources ou packaging sont modifiés
- [ ] Tests en VM ou sur matériel réel si le démarrage, l'installation, les pilotes ou les périphériques sont concernés

## Sécurité et compatibilité

- [ ] Aucun secret, fichier de clé privée ou identifiant n'est ajouté
- [ ] Aucune installation, suppression ou modification système ne se produit sans confirmation utilisateur
- [ ] Les fonctions indisponibles restent non bloquantes et ne produisent pas de mesures fictives
- [ ] Les limites et les tests non réalisés sont documentés
- [ ] Les droits des médias/ressources de marque sont connus si des assets sont ajoutés ou modifiés

## Dépendances

<!-- PR ou branches nécessaires avant celle-ci. -->

## Risques / retour arrière

<!-- Impacts connus et manière de revenir à l'état précédent. -->
