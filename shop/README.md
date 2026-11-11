# LEOS Store

Premier prototype de boutique applicative Qt Quick / PySide6.

## Fonctionnement actuel du prototype

- Catalogue initial maintenu dans `catalog.json`.
- Recherche par nom ou identifiant et filtrage par catégorie.
- Détection des applications Flatpak installées dans le profil utilisateur uniquement ; les applications système fournies par Bazzite ne sont pas proposées à la désinstallation par ce prototype.
- Fiches indiquant identifiant, source, compatibilité et information sur les dépendances.
- Vérification de disponibilité d'une application sur Flathub avant installation.
- Confirmation explicite avant installation et désinstallation.
- Opérations réalisées par Flatpak, sans gestionnaire de paquets parallèle et sans shell.

## Sécurité et limites

- L'installation n'est lancée qu'après deux étapes distinctes : confirmation de l'utilisateur, puis vérification Flathub, puis confirmation finale après vérification.
- La désinstallation n'est jamais déclenchée depuis la fiche sans dialogue de confirmation.
- Le prototype ne supprime pas automatiquement les données utilisateur et ne lance pas de nettoyage des dépendances inutilisées.
- Le catalogue est une sélection initiale et non une recherche exhaustive Flathub.
- Les descriptions, catégories et notes de compatibilité sont éditoriales ; elles ne constituent pas une certification officielle.
- Le code n'a pas encore été exécuté sur Bazzite. Le comportement de Flatpak, les modules QML et l'affichage des sorties doivent être testés dans l'image LEOS.

La boutique ne remplace ni Discover, ni Flatpak, ni les intégrations de lanceurs. Elle prépare une interface LEOS unifiée et transparente.
