# LEOS — Gaming Mode

Application Gaming plein écran construite avec **Qt 6 / QML** et **PySide6**, au-dessus de KDE.

## Éléments développés dans le prototype

- `main.py` : initialise Qt Quick et connecte les services backend.
- `qml/Main.qml` : interface plein écran avec bibliothèque par catégories, recherche, favoris, jeux récents, fiche détaillée, panneau rapide et ajout manuel. Les jaquettes manquantes ou devenues illisibles ont un visuel de remplacement à monogramme ; les sélections changent avec une transition douce.
- `backend/library.py` : bibliothèque unifiée, détection locale des jeux Steam, Heroic et Lutris, ajout manuel, favoris et historique récent.
- `backend/system_monitor.py` : CPU/RAM, températures CPU/GPU et télémétrie GPU/VRAM via les métriques DRM/hwmon exposées par le pilote Linux. Les données non fournies par le pilote restent indisponibles.
- `backend/power_profiles.py` : découverte des profils réellement proposés par `power-profiles-daemon` et application via `powerprofilesctl`, uniquement après confirmation explicite dans l'interface.
- `backend/mangohud.py` : détection facultative de MangoHud et ajout du wrapper uniquement aux commandes de lancement direct lorsque l'utilisateur active l'overlay. Aucun paquet n'est installé et aucune configuration globale n'est modifiée.
- `backend/controller.py` : relie le modèle et les services à QML, surveille les manettes compatibles et transmet les actions de navigation. Le panneau rapide est également navigable à la manette : overlay MangoHud, profils d'énergie avec confirmation, retour Desktop et fermeture. Les directions maintenues au D-pad ou au stick se répètent après un court délai, à cadence contrôlée, puis cessent dès le relâchement.
- `backend/instance_lock.py` : empêche l'ouverture de plusieurs fenêtres Gaming dans la même session utilisateur. Le verrou non bloquant est placé dans le répertoire d'exécution utilisateur, libéré à la fermeture et récupéré après un arrêt anormal ; il ne termine aucun autre processus.
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
- Les introductions vidéo de transition Desktop/Gaming sont connectées à Qt Multimedia ; les pistes AAC intégrées suivent le réglage sonore LEOS et un repli évite de bloquer la transition. Les animations propres au lancement de chaque jeu, les fiches cinématiques et les métadonnées en ligne ne sont pas encore connectées.
- La charge GPU, la VRAM et la température GPU sont lues via sysfs DRM/hwmon lorsqu'elles sont exposées (notamment sur les pilotes AMD compatibles). Le nom affiché identifie le constructeur et l'identifiant PCI, pas nécessairement le modèle commercial. L'overlay FPS s'appuie sur MangoHud lorsqu'il est installé et activé ; LEOS n'invente pas de valeur FPS et ne prétend pas intégrer un compteur interne temps réel.
- La navigation à la manette couvre les catégories, la grille, la barre de recherche, l’actualisation, l’ajout manuel et les actions de la fiche (favoris / jouer), en plus du panneau rapide. Le retour remonte d’une zone à la précédente ; les flèches restent libres pour éditer le texte de recherche. Les changements de focus au clavier actualisent aussi les repères visuels.
- Les profils d'énergie sont limités aux modes natifs détectés (Performance, Équilibré, Économie d'énergie). LEOS ne simule pas de profil silencieux distinct et ne pilote pas directement les ventilateurs ; si le service système est absent, les commandes sont désactivées.
- Les tests automatisés vérifient les fonctions Python et les contrats d'intégration QML ; l'exécution réelle de l'interface et la validation matérielle sur Bazzite restent à effectuer.
Ne pas présenter ces fonctions comme opérationnelles avant les tests correspondants.


### Fiches de jeux

La fiche d'un jeu affiche les métadonnées vérifiées par la bibliothèque : titre, plateforme, source, état des fichiers locaux et identifiant du catalogue lorsqu'il est disponible. Pour Steam, Heroic et Lutris, LEOS vérifie le dossier d'installation (et, pour Lutris, l'exécutable déclaré lorsqu'il est absolu). Une entrée conservée dans un catalogue mais dont le dossier n'est plus accessible est signalée « Fichiers absents » ; cela permet notamment d'identifier un disque externe déconnecté. Si le catalogue ne fournit aucun chemin exploitable, l'état reste « État inconnu » plutôt que d'affirmer à tort que le jeu est installé. Les entrées manuelles restent identifiées comme telles. Aucun chemin privé complet ni argument de lancement n'est exposé dans l'interface.


### Lancement et retours d'état

LEOS vérifie qu'un exécutable direct est trouvable et exécutable avant de demander son démarrage. Les adresses de protocole (par exemple `steam://`) sont transmises au gestionnaire associé via les services Qt, sans prétendre vérifier que le jeu a effectivement démarré. Pour une commande directe, LEOS indique uniquement que le processus de lancement a été créé ; le chargement complet du jeu n'est pas confirmé. Les erreurs de sélection, de commande absente, d'exécutable indisponible et de démarrage sont différenciées. Aucun shell n'est utilisé.

### Détection des lanceurs

Le panneau rapide indique la disponibilité de Steam, Heroic et Lutris à partir des exécutables natifs trouvés dans le PATH et des identifiants d'applications Flatpak installés. Cette détection décrit la présence du lanceur sur l'hôte ; elle ne garantit ni sa connexion à un compte, ni le démarrage d'un jeu. Les jeux importés restent limités aux catalogues locaux documentés ci-dessus.

La disponibilité des lanceurs est réévaluée périodiquement pendant Gaming Mode (toutes les 15 secondes) ; l'interface n'affiche un changement que si l'état détecté diffère. En cas d'échec de lancement, la notification reprend le motif précis présenté dans l'interface, plutôt qu'un message générique. La recherche accepte aussi l'App ID Steam et l'identifiant stable d'une entrée importée.


### Cohérence des catalogues et chemins

Les titres sont normalisés à l'affichage en supprimant uniquement les espaces de début/fin et les répétitions d'espaces ; la casse et la ponctuation du nom d'origine sont conservées. La recherche ignore les différences de casse et d'accents et tolère les espaces répétés. LEOS signale les titres strictement identiques entre plusieurs entrées comme « doublons potentiels » en indiquant les sources concernées, sans les fusionner ni les supprimer. Les marqueurs d'édition (Deluxe, GOTY, Remastered, etc.) sont conservés dans la comparaison afin de ne pas confondre des versions distinctes. Cet indicateur est un indice, pas une preuve que deux entrées correspondent au même produit.

Les manifestes Steam ne peuvent fournir un chemin d'installation que si le nom de dossier est un simple composant sûr (sans séparateur ni référence au dossier parent). Les entrées Heroic dont le chemin est absent restent visibles avec un état « État inconnu ». LEOS ne fusionne pas deux entrées provenant de lanceurs différents sur la seule base d'un titre identique : des éditions ou installations distinctes peuvent porter le même nom. Les doublons d'identifiant au sein d'une même source sont, eux, neutralisés par l'identifiant stable du catalogue. Le chargement de chaque fournisseur est isolé : une erreur d'accès à un catalogue ou à une jaquette ne bloque pas l'import des autres lanceurs. Une jaquette indisponible est simplement omise ; les entrées de jeu valides continuent d'être affichées.


## Fonds d'écran de référence

Le dépôt fournit un fond Gaming 4K dans `branding/wallpapers/gaming-leos.svg`. Il réutilise directement `branding/gaming-logo.jpeg` par référence relative, sans créer une version altérée de l'emblème. Le fichier est empaqueté avec les autres ressources LEOS ; il reste une ressource sélectionnable via les paramètres natifs KDE et n'est pas appliqué automatiquement à l'arrière-plan de l'application Gaming. Le rendu SVG lié attend encore une validation sur Bazzite.
