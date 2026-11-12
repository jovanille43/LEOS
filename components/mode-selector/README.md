# LEOS — Mode Selector

Le Mode Selector est le point d'entrée visuel permettant de choisir entre Desktop Mode et Gaming Mode. Il s'agit d'un composant commun aux deux expériences.

## Présentation

- Afficher deux grandes cartes côte à côte : Desktop et Gaming.
- Utiliser exclusivement l'emblème officiel du lion seul pour Desktop.
- Utiliser exclusivement l'emblème officiel du lion avec manette pour Gaming.
- Respecter l'identité LEOS : fond noir, lion métallique, éclairages cyan et magenta et typographie officielle.
- Mettre en évidence clairement le mode sélectionné et l'action de validation.

L'image comparative des deux emblèmes est une référence de conception uniquement : elle ne doit pas être utilisée comme visuel principal du sélecteur. Chaque carte utilise son emblème individuel.

## Commandes

Le sélecteur doit être utilisable avec :
- manette : stick gauche ou croix directionnelle pour naviguer, A/Croix pour valider, B/Rond pour revenir ;
- clavier : flèches pour naviguer, Entrée pour valider, Échap pour revenir ;
- souris : clic sur une carte puis validation.

Le sélecteur réutilise le backend evdev en lecture seule et les profils sauvegardés dans LEOS Controller Center. La navigation par croix directionnelle ou stick, validation et retour est intégrée au code ; les essais sur plusieurs modèles de manettes restent à effectuer.

## Transition

- **Choix Desktop :** l'introduction Desktop est jouée, puis le sélecteur se ferme et laisse apparaître le bureau KDE déjà actif.
- **Entrée Gaming :** une confirmation explique que les applications ouvertes resteront en arrière-plan. Après validation, l'introduction Gaming est jouée puis l'application plein écran est lancée.
- **Retour Desktop :** une confirmation est demandée depuis Gaming ; après validation, l'introduction Desktop est jouée puis Gaming se ferme.
- Aucune application ouverte n'est terminée automatiquement par LEOS.
- Si la lecture vidéo échoue ou dépasse son délai de sécurité, la transition se termine quand même.

## Animation et son

- `desktop-intro.mov` accompagne le choix Desktop et le retour depuis Gaming.
- `gaming-intro.mp4` accompagne chaque entrée dans Gaming Mode ; l'animation du lion avec manette est la référence principale.
- `gaming-roar-reference.mp4` est conservée comme référence secondaire et n'est pas jouée automatiquement.
- Les vidéos sont lues par Qt Multimedia avec leurs pistes audio intégrées. Les réglages LEOS permettent de désactiver séparément les animations et les sons.
- Le délai de sécurité du lecteur évite de bloquer la transition si le décodage ou la lecture ne se termine pas correctement.
## Comportement et accessibilité

- À chaque ouverture de session KDE, affichage du sélecteur après authentification. Le dernier mode utilisé est rappelé à l'écran, mais ne démarre pas automatiquement.
- Possibilité d'ouvrir le sélecteur à tout moment depuis les deux modes.
- Raccourcis directs prévus : `Super + G` pour Gaming et `Super + D` pour Desktop.
- Un raccourci personnalisable doit également permettre d'ouvrir le sélecteur.
- Prévoir un état de focus visible, des libellés lisibles et une navigation cohérente.

## Architecture et limites

Le sélecteur doit déclencher une transition contrôlée vers l'environnement cible. Il ne doit pas être considéré comme une simple fenêtre graphique : le lancement, l'arrêt ou la conservation des sessions dépendra de l'architecture de session KDE et de l'environnement gaming retenu.

Le lancement de Gaming et le retour vers Desktop sont raccordés à la session KDE existante. Les animations officielles et leurs pistes audio sont intégrées au code ; leur lecture effective et le comportement des applications en arrière-plan doivent encore être testés dans une vraie session Bazzite. Les raccourcis globaux KDE restent à intégrer.

## État

Sélecteur fonctionnel côté code : écran plein écran, horloge/date, rappel du dernier mode, cartes Desktop/Gaming et navigation souris/clavier/manette. Les emblèmes JPEG officiels et les vidéos Desktop/Gaming sont présents dans `branding/` et leurs chemins sont raccordés au code. Les essais de restitution en session KDE réelle restent à faire.
