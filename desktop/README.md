# LEOS — Desktop Mode

Desktop Mode conserve **KDE Plasma** comme bureau principal. LEOS ajoute progressivement une identité cohérente sans remplacer les mécanismes natifs de KDE/Bazzite.

## Éléments déjà préparés

- `applications/leos-mode-selector.desktop` : entrée de menu pour ouvrir le sélecteur Desktop/Gaming.
- `autostart/leos-session.desktop` : point d'entrée de session qui restaure Gaming si ce mode était le dernier utilisé. En mode Desktop, il se ferme sans action.
- `config/desktop-defaults.json` : profil déclaratif LEOS Original (palette sombre cyan/magenta, dock inférieur, applications épinglées indicatives et widgets facultatifs).

## Direction visuelle Desktop

- Emblème officiel du lion seul, dès que le fichier source sera ajouté au dépôt.
- Fond sombre LEOS, accents cyan et magenta, surfaces sobres et contrastes lisibles.
- Dock inférieur centré, personnalisable et désactivable.
- Widgets facultatifs, désactivés par défaut.
- Menu LEOS donnant accès aux applications, à la recherche, aux modes et au Centre de contrôle.

## Règles de personnalisation

Le profil JSON est une référence de conception, pas une configuration Plasma directement applicable. Il ne doit pas être présenté comme un thème déjà installé ou actif. L'application future devra sauvegarder les réglages KDE existants, vérifier les applications disponibles et demander le consentement avant toute modification du profil personnel.

Aucune configuration Plasma existante ne sera écrasée silencieusement.

## À finaliser

- Intégration de l'emblème et du fond d'écran officiels.
- Moteur de thème et configurateur du dock, avec sauvegarde/restauration.
- Menu principal LEOS et recherche universelle.
- Raccourcis globaux KDE personnalisables (dont Super+G / Super+D).
- Tests de session sur une vraie installation Bazzite KDE.

Le packaging installe les ressources de référence sous `/usr/share/leos/`. Les personnalisations Plasma avancées seront appliquées au profil utilisateur uniquement après validation explicite.
