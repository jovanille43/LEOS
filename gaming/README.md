# LEOS — Gaming Mode

Application Gaming plein écran construite avec **Qt 6 / QML** et **PySide6**, au-dessus de KDE.

## Éléments développés dans le prototype

- `main.py` : initialise Qt Quick et connecte les services backend.
- `qml/Main.qml` : interface plein écran avec bibliothèque par catégories, recherche, favoris, jeux récents, fiche détaillée, panneau rapide et ajout manuel.
- `backend/library.py` : bibliothèque unifiée, détection locale des jeux Steam, Heroic et Lutris, ajout manuel, favoris et historique récent.
- `backend/system_monitor.py` : CPU/RAM et température CPU si les capteurs sont disponibles. Les valeurs non disponibles sont affichées comme indisponibles.
- `backend/controller.py` : relie le modèle et les services à QML, surveille les manettes compatibles et transmet les actions de navigation.
- `requirements.txt` : dépendances du prototype.

Les jeux Steam sont lancés via l'URL `steam://rungameid/...` lorsqu'un gestionnaire de protocole est installé. Les jeux ajoutés manuellement sont lancés avec une liste d'arguments, sans shell.

## Développement local

Depuis le dossier `gaming/` :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Le code nécessite les modules Qt Quick et Qt Quick Controls de Qt 6 sur l'hôte.

## Limites connues

- Les fournisseurs automatiques actuels couvrent Steam, les installations Heroic (Epic, GOG et Amazon Games) et Lutris ; les autres lanceurs ne sont pas encore importés.
- Les jaquettes sont recherchées dans les caches locaux Steam et Lutris. Aucune image n'est téléchargée et l'absence d'illustration est signalée dans l'interface.
- Les métadonnées en ligne, les fiches cinématiques et les animations de lancement ne sont pas encore connectées.
- Le GPU, les températures GPU et le FPS en jeu nécessitent des intégrations dédiées ; les valeurs non disponibles ne sont pas simulées.
- La navigation à la manette couvre les directions, la validation, le retour et le panneau rapide. Les raccourcis globaux du système restent à définir.
- Les tests automatisés vérifient les fonctions Python et les contrats d'intégration QML ; l'exécution réelle de l'interface et la validation matérielle sur Bazzite restent à effectuer.
Ne pas présenter ces fonctions comme opérationnelles avant les tests correspondants.
