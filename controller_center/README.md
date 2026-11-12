# LEOS Controller Center

Le Centre des manettes détecte les contrôleurs Linux compatibles via `evdev` et affiche les entrées en temps réel.

## Fonctions du prototype

- Détection USB et Bluetooth par les nœuds Linux `/dev/input/event*`.
- Ouverture des périphériques strictement en lecture seule et lecture non bloquante.
- Profils Automatique, Standard, Xbox, PlayStation, Nintendo et Personnalisé.
- Préférences par contrôleur : profil, zone morte et centres neutres des axes.
- Affichage des boutons actuellement maintenus, des relâchements et des valeurs des axes.
- Effacement de l'état des boutons lorsqu'une manette est déconnectée ou remplacée.
- Stockage des préférences dans le profil utilisateur Linux, avec écriture atomique et permissions privées.

## État des boutons

Le panneau « Boutons maintenus » reflète l'état courant : un événement d'appui ajoute un bouton, un événement de relâchement le retire, et une déconnexion vide l'ensemble. Tous les événements reçus dans un même lot sont traités dans l'ordre, y compris une pression suivie d'un relâchement entre deux rafraîchissements de l'interface. Les répétitions d'événements n'ajoutent pas de nouveaux appuis. La zone « Dernière entrée » reste un historique instantané du dernier événement reçu.

## Limites

Les profils et centres d'axes sont enregistrés dans LEOS, mais ne remappent pas encore les commandes à l'intérieur des jeux. Steam et les lanceurs conservent leur propre configuration. La compatibilité de chaque modèle de manette, notamment Bluetooth, doit être validée sur une session Bazzite réelle.

LEOS ne saisit pas les périphériques, ne modifie pas les règles udev, n'envoie aucun événement et ne change pas les mappings globaux du système.
