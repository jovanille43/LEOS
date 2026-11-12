# LEOS Store

Premier prototype de boutique applicative Qt Quick / PySide6.

## Fonctionnement actuel du prototype

- Catalogue initial maintenu dans `catalog.json`.
- Recherche insensible à la casse et aux accents, tolérante aux espaces répétés, sur le nom, l'identifiant, la catégorie, la description et la source ; filtrage complémentaire par catégorie.
- Détection séparée des installations Flatpak utilisateur et système ; la fiche distingue les deux portées et avertit lorsqu'une désinstallation système peut demander une autorisation administrateur.
- Fiches indiquant identifiant, source, compatibilité et information sur les dépendances.
- Vérification de l'adresse du dépôt Flathub du profil utilisateur avant toute requête de métadonnées ; seules les URL HTTPS canoniques Flathub sont acceptées. Lecture du runtime déclaré dans les métadonnées lorsque disponible.
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
