# LEOS Desktop layouts

Les dispositions Desktop sont des profils déclaratifs destinés au futur configurateur LEOS. Elles décrivent l'apparence souhaitée ; elles ne sont pas des fichiers de configuration Plasma directement applicables.

## Principes

- KDE Plasma reste le bureau et le gestionnaire de fenêtres.
- Le profil LEOS Original privilégie un fond sombre, des accents cyan/magenta et un dock inférieur centré.
- Les widgets sont facultatifs et désactivés par défaut.
- Les applications épinglées sont des identifiants indicatifs : le configurateur devra vérifier qu'elles sont installées avant de les proposer.
- L'utilisateur peut modifier ou désactiver le dock, les widgets, les animations et les couleurs.
- Aucun fichier de configuration Plasma existant ne doit être écrasé silencieusement.

Le profil partagé est défini dans `config/desktop-defaults.json`. Il s'agit d'une référence de conception, pas encore d'un moteur d'application de thème. L'application automatique sera ajoutée uniquement avec une sauvegarde préalable et un choix explicite de l'utilisateur.
