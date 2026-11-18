# LEOS Store

Premier prototype de boutique applicative Qt Quick / PySide6.

## Fonctionnement actuel du prototype

- Catalogue initial maintenu dans `catalog.json`.
- Recherche insensible à la casse et aux accents, tolérante aux espaces répétés, sur le nom, l'identifiant, la catégorie, la description et la source ; filtrage complémentaire par catégorie.
- Détection séparée des installations Flatpak utilisateur et système ; la fiche distingue les deux portées et avertit lorsqu'une désinstallation système peut demander une autorisation administrateur.
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


## Sélection d'émulation V2

La catégorie **Émulation** référence les applications suivantes, installables séparément à la demande :

| Application | Plateforme principale | Identifiant Flathub |
| --- | --- | --- |
| RetroArch | Multi-systèmes / libretro | `org.libretro.RetroArch` |
| Dolphin Emulator | GameCube / Wii | `org.DolphinEmu.dolphin-emu` |
| PCSX2 | PlayStation 2 | `net.pcsx2.PCSX2` |
| PPSSPP | PlayStation Portable | `org.ppsspp.PPSSPP` |
| melonDS | Nintendo DS / DSi | `net.kuribo64.melonDS` |
| RPCS3 | PlayStation 3 | `net.rpcs3.RPCS3` |

Les six fiches ne sont pas marquées comme préinstallées. Chaque installation passe par le contrôle Flathub et les confirmations existantes de la boutique. Dolphin et RPCS3 utilisent des paquets communautaires Flathub non vérifiés par les projets amont ; cet avertissement est visible dans leur fiche.

La boutique n'installe aucun jeu, ROM, BIOS, firmware, clé ou cœur RetroArch. La présence d'un émulateur installé ne signifie pas encore que LEOS importe automatiquement ses jeux dans Gaming Mode. Le plan des prochaines étapes (détection explicite des dossiers, validation des chemins, lancement sans shell et précontrôles de BIOS/firmware) est suivi dans [la feuille de route d'intégration](../docs/emulator-integration.md).
