# LEOS Store

Premier prototype de boutique applicative Qt Quick / PySide6.

## Fonctionnement actuel du prototype

- Catalogue initial maintenu dans `catalog.json`.
- Recherche insensible à la casse et aux accents, tolérante aux espaces répétés, sur le nom, l'identifiant, la catégorie, la description et la source ; filtrage complémentaire par catégorie.
- Détection distincte des installations Flatpak utilisateur, système par défaut et système personnalisées. Les installations personnalisées sont signalées comme installées, mais leurs opérations restent bloquées tant que leur cible exacte n'est pas prise en charge ; elles ne sont jamais confondues avec `--system`.
- Fiches indiquant identifiant, source, compatibilité et information sur les dépendances.
- Vérification de l'adresse du dépôt Flathub du profil utilisateur avant toute requête de métadonnées ; seules les URL HTTPS canoniques Flathub sont acceptées. L'adresse exacte vérifiée est affichée dans la confirmation finale, avec le runtime déclaré dans les métadonnées lorsque disponible. L'origine est contrôlée une seconde fois juste après la confirmation finale et avant le lancement de l'installation.
- Confirmation explicite avant installation et désinstallation.
- Opérations réalisées par Flatpak, sans gestionnaire de paquets parallèle et sans shell.

## Sécurité et limites

- L'installation n'est lancée qu'après une première confirmation, la vérification de l'origine du dépôt Flathub utilisateur, la lecture des métadonnées, puis une confirmation finale après vérification.
- La désinstallation utilisateur ou système n'est jamais déclenchée depuis la fiche sans dialogue de confirmation ; la portée exacte est transmise à Flatpak.
- Le prototype ne supprime pas automatiquement les données utilisateur et ne lance pas de nettoyage des dépendances inutilisées.
- Le catalogue est une sélection initiale et non une recherche exhaustive Flathub.
- Les descriptions, catégories et notes de compatibilité sont éditoriales ; elles ne constituent pas une certification officielle. Le runtime affiché provient des métadonnées Flathub, lorsqu'il est déclaré ; il ne représente pas une liste exhaustive de tous les composants qui pourraient être installés.
- Le code n'a pas encore été exécuté sur Bazzite. Le comportement de Flatpak, les modules QML et l'affichage des sorties doivent être testés dans l'image LEOS.

La boutique ne remplace ni Discover, ni Flatpak, ni les intégrations de lanceurs. Elle prépare une interface LEOS unifiée et transparente.

## Fermeture pendant une opération

À la fermeture de la boutique, le processus Flatpak en cours est interrompu et son délai de surveillance est arrêté. Si une installation ou une désinstallation a été interrompue, LEOS ne prétend pas connaître son résultat : actualise l'inventaire Flatpak avant de relancer une opération. Le nettoyage est également appelé si l'interface QML ne peut pas démarrer.
