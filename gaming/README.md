# LEOS — Gaming Mode

Application Gaming plein écran construite avec **Qt 6 / QML** et **PySide6**, au-dessus de KDE.

## Éléments développés dans le prototype

- `main.py` : initialise Qt Quick et connecte les services backend.
- `qml/Main.qml` : première interface plein écran avec bibliothèque, fiche de jeu, panneau rapide et formulaire d'ajout manuel.
- `backend/library.py` : modèle de bibliothèque, détection initiale des jeux Steam à partir des fichiers `appmanifest_*.acf`, ajout manuel et lancement configuré.
- `backend/system_monitor.py` : CPU/RAM et température CPU si les capteurs sont disponibles. Les valeurs non disponibles sont affichées comme indisponibles.
- `backend/controller.py` : relie le modèle et les services à QML.
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

- La détection automatique est actuellement limitée aux manifestes Steam locaux.
- Heroic, Lutris et les autres plateformes n'ont pas encore de fournisseurs de bibliothèque.
- Les jaquettes, métadonnées en ligne, fiches cinématiques et animations de lancement ne sont pas encore connectées.
- Le GPU, les températures GPU et le FPS en jeu nécessitent des intégrations dédiées.
- La navigation manette et les raccourcis globaux ne sont pas encore implémentés.
- Le prototype n'a pas encore été exécuté ni testé sur Bazzite.

Ne pas présenter ces fonctions comme opérationnelles avant les tests correspondants.
