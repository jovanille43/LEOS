# LEOS — Gaming Mode

Application Gaming plein écran construite avec **Qt 6 / QML** et **PySide6**, au-dessus de KDE.

## Éléments développés dans le prototype

- `main.py` : initialise Qt Quick et connecte les services backend.
- `qml/Main.qml` : interface plein écran avec bibliothèque par catégories, recherche, favoris, jeux récents, fiche détaillée, panneau rapide et ajout manuel.
- `backend/library.py` : bibliothèque unifiée, détection locale des jeux Steam, Heroic et Lutris, ajout manuel, favoris et historique récent.
- `backend/system_monitor.py` : CPU/RAM, températures CPU/GPU et télémétrie GPU/VRAM via les métriques DRM/hwmon exposées par le pilote Linux. Les données non fournies par le pilote restent indisponibles.
- `backend/power_profiles.py` : découverte des profils réellement proposés par `power-profiles-daemon` et application via `powerprofilesctl`, uniquement après confirmation explicite dans l'interface.
- `backend/mangohud.py` : détection facultative de MangoHud et ajout du wrapper uniquement aux commandes de lancement direct lorsque l'utilisateur active l'overlay. Aucun paquet n'est installé et aucune configuration globale n'est modifiée.
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
- Les jaquettes sont recherchées dans les caches locaux Steam et Lutris, ainsi que dans les chemins d'images locaux explicitement référencés par les manifestes Heroic. Aucune image n'est téléchargée ; les URL distantes et formats non pris en charge sont ignorés.
- Les métadonnées en ligne, les fiches cinématiques et les animations de lancement ne sont pas encore connectées.
- La charge GPU, la VRAM et la température GPU sont lues via sysfs DRM/hwmon lorsqu'elles sont exposées (notamment sur les pilotes AMD compatibles). Le nom affiché identifie le constructeur et l'identifiant PCI, pas nécessairement le modèle commercial. L'overlay FPS s'appuie sur MangoHud lorsqu'il est installé et activé ; LEOS n'invente pas de valeur FPS et ne prétend pas intégrer un compteur interne temps réel.
- La navigation à la manette couvre les directions, la validation, le retour et le panneau rapide. Les raccourcis globaux du système restent à définir.
- Les profils d'énergie sont limités aux modes natifs détectés (Performance, Équilibré, Économie d'énergie). LEOS ne simule pas de profil silencieux distinct et ne pilote pas directement les ventilateurs ; si le service système est absent, les commandes sont désactivées.
- Les tests automatisés vérifient les fonctions Python et les contrats d'intégration QML ; l'exécution réelle de l'interface et la validation matérielle sur Bazzite restent à effectuer.
Ne pas présenter ces fonctions comme opérationnelles avant les tests correspondants.
