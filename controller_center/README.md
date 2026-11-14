# LEOS Controller Center

Le Centre des manettes détecte les contrôleurs Linux compatibles via `evdev` et affiche les entrées en temps réel.

## Fonctions du prototype

- Détection USB et Bluetooth par les nœuds Linux `/dev/input/event*`.
- Ouverture des périphériques strictement en lecture seule et lecture non bloquante.
- Profils Automatique, Standard, Xbox, PlayStation, Nintendo et Personnalisé.
- Préférences par contrôleur : profil, zone morte et centres neutres des axes, enregistrés séparément pour chaque périphérique.
- Aperçu visuel en direct des sticks gauche et droit, normalisé de -100 à +100 selon les plages exposées par le pilote.
- Prise en compte du centre neutre calibré et de la zone morte dans l'aperçu, sans modifier les entrées transmises aux jeux.
- Affichage des boutons actuellement maintenus, des relâchements et des valeurs brutes des axes.
- Effacement de l'état des boutons lorsqu'une manette est déconnectée ou remplacée.
- Stockage des préférences dans le profil utilisateur Linux, avec écriture atomique et permissions privées.

## État des boutons

Le panneau « Boutons maintenus » reflète l'état courant : un événement d'appui ajoute un bouton, un événement de relâchement le retire, et une déconnexion vide l'ensemble. Tous les événements reçus dans un même lot sont traités dans l'ordre, y compris une pression suivie d'un relâchement entre deux rafraîchissements de l'interface. Les répétitions d'événements n'ajoutent pas de nouveaux appuis. La zone « Dernière entrée » reste un historique instantané du dernier événement reçu.

## Aperçu des sticks

Les deux sticks sont représentés par un repère circulaire. Le point suit les axes `ABS_X/ABS_Y` et `ABS_RX/ABS_RY` lorsqu'ils sont exposés par la manette. Les plages min/max du pilote sont normalisées séparément sur chaque moitié de l'axe ; les centres sauvegardés et la zone morte LEOS ne servent qu'à cet aperçu. Pour calibrer le neutre, laisse les sticks au repos puis utilise « Enregistrer le neutre ».

## Limites

Les profils et centres d'axes sont enregistrés dans LEOS, mais ne remappent pas encore les commandes à l'intérieur des jeux. Steam et les lanceurs conservent leur propre configuration. La compatibilité de chaque modèle de manette, notamment Bluetooth, doit être validée sur une session Bazzite réelle.

LEOS ne saisit pas les périphériques, ne modifie pas les règles udev, n'envoie aucun événement et ne change pas les mappings globaux du système.
