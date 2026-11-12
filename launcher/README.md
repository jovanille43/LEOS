# LEOS Mode Launcher

Ce dossier contient le sélecteur Desktop/Gaming et le point d'entrée de session.

- `main.py --select` ouvre le sélecteur plein écran.
- L'autostart KDE appelle désormais `main.py --select` à chaque ouverture de session : l'utilisateur choisit explicitement Desktop ou Gaming.
- Le dernier mode utilisé est mémorisé et affiché sur l'écran de choix.
- `main.py` sans argument conserve un mode de restauration technique : il ouvre Gaming si le dernier mode enregistré est Gaming, sinon laisse KDE afficher le bureau.
- `mode_manager.py` valide les deux modes autorisés et stocke la préférence via `leos_core`.

## Parcours de démarrage

1. Bazzite démarre et l'utilisateur ouvre sa session KDE.
2. L'écran LEOS apparaît avec l'heure, la date, le dernier mode utilisé et les deux grandes cartes.
3. Desktop ouvre le bureau KDE ; Gaming lance l'application LEOS plein écran.
4. En quittant Gaming vers Desktop, l'application se ferme et le bureau KDE déjà actif réapparaît.

Le sélecteur est un écran de choix **après l'ouverture de session KDE**. Il ne remplace pas l'écran de connexion SDDM et ne modifie pas la séquence de démarrage système.

La navigation fonctionne à la souris, au clavier et avec les manettes reconnues par le backend evdev en lecture seule. Les profils et zones mortes enregistrés dans LEOS Controller Center sont réutilisés ; aucun remappage global des entrées Linux n'est effectué.

## Sécurité des transitions

- Les applications KDE ne sont jamais terminées automatiquement.
- L'entrée vers Gaming explique que les applications restent en arrière-plan ; aucune stratégie de fermeture automatique n'est activée.
- Si le point d'entrée Gaming est absent, le sélecteur reste affiché et indique l'erreur.
- Lancement du jeu et des applications avec des arguments séparés, sans shell.

## Limites à ce stade

- Les raccourcis du sélecteur sont des raccourcis de fenêtre, pas encore des raccourcis globaux KDE.
- Le sélecteur joue `gaming-intro.mp4` avant d'ouvrir Gaming et `desktop-intro.mp4` avant de revenir au bureau. Les pistes AAC sont lues avec la vidéo et peuvent être coupées indépendamment des animations.
- Le retour depuis Gaming joue également l'introduction Desktop avant de fermer l'application.
- Les binaires JPEG/MP4 officiels ne sont pas encore présents dans l'arbre GitHub. Si un fichier est absent, si le décodage échoue ou si le lecteur dépasse son délai de sécurité, LEOS poursuit la transition sans rester bloqué.
- Le sélecteur, le rendu vidéo, le son et les transitions doivent encore être testés dans une session Bazzite KDE réelle.

## Notifications des modes LEOS

Le choix de Desktop est enregistré par le sélecteur. Pour Gaming, le dernier mode et la notification de démarrage ne sont enregistrés qu'après le chargement réussi de la fenêtre QML ; un échec de chargement ne marque donc pas Gaming comme dernier mode utilisé. Le contrôleur Gaming enregistre également la demande de retour vers Desktop. Ces événements sont persistants et non intrusifs : ils ne déclenchent pas de fenêtre au-dessus d'un jeu.
