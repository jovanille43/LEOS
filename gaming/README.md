# LEOS — Gaming Mode

Application Gaming plein écran construite avec **Qt 6 / QML** et **PySide6**. Elle s'exécute au-dessus de KDE, qui reste actif en arrière-plan.

## Premier prototype

Le dépôt contient maintenant :
- `main.py` : point d'entrée PySide6 et chargement de QML ;
- `qml/Main.qml` : premier squelette visuel plein écran ;
- `requirements.txt` : dépendance PySide6.

Pour lancer le prototype depuis ce dossier, dans un environnement Python disposant de Qt 6 :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Sur une distribution Linux, les bibliothèques Qt système et le support graphique doivent être disponibles. Le prototype n'a pas encore été exécuté ni testé sur matériel.

## Prochaines étapes

1. Tester le lancement sous Bazzite KDE.
2. Remplacer les contenus provisoires par les composants de navigation LEOS.
3. Construire la bibliothèque unifiée et ses intégrations.
4. Ajouter les transitions cinématiques, le panneau rapide et les contrôles.

Les fonctions de bibliothèque et les intégrations de lanceurs ne sont pas encore implémentées.
