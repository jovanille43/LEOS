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

Les correspondances exactes des boutons devront être vérifiées avec les manettes et la couche d'entrée Linux prises en charge.

## Transition

Après sélection d'un autre mode, LEOS doit demander quoi faire des applications ouvertes :
- conserver les applications en arrière-plan, lorsque l'architecture et les applications le permettent ;
- fermer proprement les applications avant de poursuivre.

Aucune application ne doit être fermée sans consentement explicite. La conservation en arrière-plan ne doit pas être promise pour les applications qui ne la prennent pas en charge.

## Animation et son

- Desktop : animation sobre du lion seul.
- Gaming : animation officielle du lion qui croque la manette, utilisée à chaque entrée dans Gaming Mode.
- La signature sonore de transition est synchronisée avec l'animation.
- Les animations et les sons doivent pouvoir être désactivés individuellement dans les paramètres.

Les fichiers de référence fournis par le projet seront ajoutés dans `branding/` lorsqu'ils seront disponibles dans le dépôt.

## Comportement et accessibilité

- Démarrage sur le dernier mode utilisé, selon la préférence retenue pour LEOS.
- Possibilité d'ouvrir le sélecteur à tout moment depuis les deux modes.
- Raccourcis directs prévus : `Super + G` pour Gaming et `Super + D` pour Desktop.
- Un raccourci personnalisable doit également permettre d'ouvrir le sélecteur.
- Prévoir un état de focus visible, des libellés lisibles et une navigation cohérente.

## Architecture et limites

Le sélecteur doit déclencher une transition contrôlée vers l'environnement cible. Il ne doit pas être considéré comme une simple fenêtre graphique : le lancement, l'arrêt ou la conservation des sessions dépendra de l'architecture de session KDE et de l'environnement gaming retenu.

La faisabilité des transitions, de la gestion des applications et des animations devra être testée sur une première image LEOS.

## État

Spécification initiale créée. Le sélecteur n'est pas encore implémenté.
