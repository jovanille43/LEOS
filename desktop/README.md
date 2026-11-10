# LEOS — Desktop Mode

Desktop Mode conserve **KDE Plasma** comme bureau principal. Les personnalisations LEOS seront ajoutées progressivement sans remplacer les mécanismes natifs de KDE.

## Intégration préparée

- `applications/leos-mode-selector.desktop` : entrée de menu pour ouvrir le sélecteur Desktop/Gaming.
- `autostart/leos-session.desktop` : point d'entrée de session qui restaure Gaming si ce mode était le dernier utilisé. En mode Desktop, il se ferme sans action.

Le packaging BlueBuild installe ces fichiers dans les emplacements système appropriés.

## À finaliser

- Identité graphique officielle Desktop et configuration Plasma.
- Menu principal LEOS et dock avec dispositions personnalisables.
- Raccourcis globaux KDE Super+G / Super+D.
- Tests d'autostart et de transition dans une session KDE réelle.

Aucune configuration Plasma n'est encore forcée dans le profil personnel de l'utilisateur.
