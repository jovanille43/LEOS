# LEOS 🦁

**LEOS** est une distribution Linux personnalisée basée sur **Bazzite KDE**. Son objectif est de réunir une expérience de bureau élégante et un environnement gaming immersif au sein d'un seul système.

> **État du projet :** prototype en développement. Le dépôt contient les applications sources (Gaming, sélecteur de modes, Centre de contrôle, Centre des manettes et boutique), les ressources visuelles officielles et les introductions vidéo. Les applications doivent encore être validées sur une session Bazzite réelle et intégrées dans une image installable.

## Vision

LEOS propose deux expériences au sein d'une seule installation :

- **Desktop Mode** — bureau KDE personnalisé, avec l'emblème LEOS représentant le lion seul.
- **Gaming Mode** — application LEOS plein écran au-dessus de KDE, pensée pour la manette, avec l'emblème du lion tenant une manette.

Les deux modes partagent le même système, les mêmes fichiers, applications, pilotes et services. Le passage d'un mode à l'autre se fait sans redémarrage. À chaque transition vers Gaming ou retour vers Desktop, LEOS demande une confirmation ; les applications ouvertes restent en arrière-plan et ne sont jamais fermées automatiquement.

## Identité visuelle

L'identité LEOS repose sur un lion métallique, des éclairages cyan et magenta, une typographie dédiée et un fond noir.

- Desktop : emblème officiel du lion seul.
- Gaming : emblème officiel du lion avec manette.
- Les animations et sons LEOS seront configurables et désactivables.

Les références visuelles fournies pour le projet doivent être respectées. L'image comparative des deux emblèmes sert de référence et ne doit pas devenir le visuel principal d'un écran.

## Base technique

| Élément | Choix |
| --- | --- |
| Système de base | Bazzite KDE Desktop |
| Construction de l'image | BlueBuild |
| Interface Gaming | Qt 6 / QML avec logique applicative PySide6 |
| Interface Desktop | KDE Plasma personnalisé |
| Gestion des manettes | Linux evdev via python3-evdev |
| Dépôt | GitHub |
| Distribution visée | Image LEOS dédiée, puis ISO installable |

LEOS conserve les mécanismes natifs de Bazzite, KDE et Linux. Les composants spécifiques au projet complètent cette base sans créer de gestionnaires concurrents ni contourner le modèle immuable de Bazzite.

### Composants source présents dans le dépôt

- **Gaming Mode** : bibliothèque locale unifiée avec imports Steam, Heroic (Epic, GOG et Amazon Games) et Lutris, ajout manuel, favoris, jeux récents, recherche et navigation clavier/manette.
- **Cohérence de bibliothèque** : titres nettoyés sans réécriture de leur capitalisation, recherche tolérante aux accents et aux espaces répétés, signalement prudent des titres identiques entre sources. Les entrées ne sont jamais fusionnées ou supprimées automatiquement.
- **Métadonnées de jeu** : source, identifiant de catalogue, jaquette locale lorsqu'elle existe et état d'installation vérifié. Les chemins privés et commandes de lancement ne sont pas exposés dans la fiche QML.
- **Télémétrie Gaming** : mesures CPU/RAM et informations GPU/VRAM/température uniquement lorsque les interfaces DRM/hwmon du pilote les exposent. L'overlay FPS repose sur MangoHud s'il est présent ; LEOS n'invente pas de mesures.
- **Sélecteur Desktop/Gaming** : modes au sein d'une seule session KDE, dernier mode mémorisé et navigation par clavier/manette ; les transitions doivent encore être validées en session réelle.
- **Centre de contrôle LEOS** : pages matériel et connexions, diagnostic système, nettoyage avec aperçu et confirmation, mises à jour, notifications et réseau. Les inventaires matériels et diagnostics sont en lecture seule ; les réglages système s'appuient sur les outils natifs.
- **Centre des notifications LEOS** : historique local des événements émis par les composants LEOS. Les notifications système natives et leur historique restent gérés par Plasma ; les événements LEOS en Gaming sont conservés silencieusement pour ne pas interrompre une partie.
- **Centre des manettes** : détection, test des boutons/axes et profils de navigation LEOS, sans modifier globalement les mappings Linux ou ceux des jeux externes.
- **Boutique LEOS** : catalogue curaté, inventaire Flatpak utilisateur/système, confirmation avant toute opération, vérification Flathub avant installation et affichage du runtime déclaré lorsqu'il est présent dans les métadonnées.
- **Applications initiales** : Brave, LibreOffice et VLC sont prévues pour une installation unique en Flatpak utilisateur ; le marqueur empêche leur réinstallation automatique après désinstallation.
- **Validation continue** : workflows GitHub Actions pour compiler les sources Python, exécuter les tests et contrôler la recette BlueBuild.

Ces éléments sont des prototypes source. Les tests automatisés et les contrôles de recette ne remplacent pas l'exécution des applications sur une session Bazzite réelle, les vérifications matérielles ni la construction d'une image installable.

## Gaming Mode

- Application LEOS plein écran au-dessus de KDE ; KDE reste actif en arrière-plan.
- Interface utilisable à la manette, au clavier et à la souris.
- Bibliothèque locale organisée en catégories PC Gaming, Nintendo, PlayStation, SEGA et Arcade. Les catégories console/arcade sont prêtes pour les futures intégrations ; l'import automatique actuel concerne Steam, Heroic et Lutris.
- Recherche par titre, plateforme ou source, insensible à la casse et aux accents, et tolérante aux espaces répétés.
- Favoris et historique des jeux récemment lancés, conservés dans le profil utilisateur.
- Navigation clavier et manette, avec confirmation/retour et commandes adaptées aux profils contrôleur pris en charge.
- Imports Steam (bibliothèques principales et secondaires), Heroic (Epic, GOG et Amazon Games) et Lutris ; ajout manuel de commandes de lancement.
- Jaquettes recherchées dans les caches locaux Steam/Lutris et les fichiers explicitement référencés par Heroic. Aucune image distante n'est téléchargée.
- Fiche de jeu : titre, plateforme, source, statut des fichiers locaux et identifiant catalogue ; chemins privés et arguments de lancement restent masqués.
- Signalement des doublons potentiels par correspondance exacte de titre normalisé. Les éditions sont préservées et aucune entrée n'est fusionnée ou supprimée.
- Panneau rapide, statistiques système réelles et profils d'énergie natifs disponibles lorsque les services matériels correspondants existent.
- MangoHud peut être ajouté aux commandes de lancement direct lorsqu'il est installé et activé. LEOS ne présente pas de compteur FPS interne fictif.
- Les introductions vidéo Desktop/Gaming sont raccordées à Qt Multimedia, avec son intégré, réglage sonore indépendant et repli en cas d'erreur. Les trois vidéos sont présentes dans `branding/animations/` (Desktop en MOV, Gaming en MP4) ; leur décodage et leur restitution audio doivent encore être validés sur Bazzite. Les intégrations d'émulateurs restent à développer.

## Desktop Mode

- Bureau KDE personnalisé avec l'identité LEOS.
- Menu principal LEOS avec recherche, catégories, favoris et applications récemment utilisées. Les préférences de dock et profils de disposition sont préparés, mais leur application au véritable panneau Plasma reste désactivée.
- Notifications natives et historique système restent gérés par Plasma ; le Centre LEOS conserve uniquement les événements émis par les applications et services LEOS.
- Centre de contrôle simplifié pour les fonctions propres à LEOS, avec tableau de bord matériel en lecture seule et accès direct aux paramètres KDE avancés.
- Palettes LEOS configurables dans les interfaces LEOS ; le schéma de couleurs KDE et le Plasma Style peuvent être appliqués séparément après confirmation. Les fonds d'écran restent à intégrer. Les animations Desktop/Gaming sont raccordées et leurs fichiers sont présents dans le dépôt ; la validation du rendu vidéo et audio sur une session Bazzite réelle reste à effectuer.

## Bluetooth

Le Bluetooth est pris en charge comme fonctionnalité attendue dans Desktop Mode et Gaming Mode : manettes, casques, écouteurs, enceintes, claviers et souris compatibles. LEOS réutilise la pile BlueZ, les paramètres KDE et PipeWire de Bazzite ; il ne lance pas de gestionnaire parallèle. Le Centre de contrôle offrira un accès rapide, tandis que l'association et le dépannage complets resteront accessibles dans KDE. Le Gaming Mode ne désactivera pas le Bluetooth lors d'un changement de mode. La validation sur matériel réel reste à effectuer ; voir [docs/bluetooth.md](docs/bluetooth.md).

## Centre des manettes

Le Centre des manettes propose une vue des contrôleurs détectés par Linux, un test des boutons et axes analogiques, la détection automatique des profils Xbox/PlayStation/Nintendo lorsqu'elle est fiable, le choix manuel d'un profil, le réglage d'une zone morte et l'enregistrement de la position neutre des axes.

Les préférences sont enregistrées dans le compte Linux de l'utilisateur et appliquées à la navigation de l'interface Gaming LEOS (profil, zone morte et calibration des sticks). Le prototype ne modifie pas les mappings du système ou des jeux externes : les configurations Steam et des lanceurs restent prioritaires.

## Applications fournies et boutique LEOS

Brave, LibreOffice et VLC sont installées une seule fois dans le profil utilisateur au premier démarrage par un service LEOS. Elles peuvent ensuite être désinstallées librement depuis la boutique ; le service mémorise que l'installation initiale a été effectuée et ne les réinstalle pas. Steam est déjà fourni par la base Bazzite Desktop. La boutique distingue les applications utilisateur et système : les deux peuvent être désinstallées depuis la boutique après confirmation ; les applications système peuvent demander une authentification administrateur. Les composants RPM/OSTree constitutifs de Bazzite restent gérés par les outils système.

La boutique proposera jeux, émulateurs, applications, utilitaires et éléments de personnalisation. Elle s'appuiera sur Flatpak/Flathub, les mécanismes natifs de Bazzite et les intégrations de lanceurs compatibles.

**Toute installation ou désinstallation exige une confirmation explicite.** Chaque fiche doit préciser le contenu de l'opération, sa source, sa compatibilité et ses éventuelles dépendances.

## Principes de sécurité et de fiabilité

- Aucune installation ou désinstallation sans confirmation.
- Aucune fermeture d'application sans choix explicite de l'utilisateur lors d'une transition.
- Les mises à jour utilisent les mécanismes natifs de Bazzite ; l'utilisateur décide de leur installation.
- Les opérations de nettoyage, suppression ou modification système demandent une confirmation.
- Les limites de compatibilité matérielle et logicielle sont indiquées clairement.

## Structure du dépôt

```text
LEOS/
├── .github/workflows/   # Automatisation et vérifications
├── branding/            # Logos, animations, sons et ressources
├── config/              # Configuration partagée de LEOS
├── controller_center/   # Gestion et test des manettes
├── control_center/      # Paramètres LEOS
├── desktop/             # Personnalisation du Desktop Mode
├── docs/                # Architecture et documentation
├── gaming/              # Application Gaming LEOS
├── shop/                # Boutique LEOS et opérations Flatpak confirmées
├── recipes/             # Recette BlueBuild
└── README.md
```

## Prochaines étapes

1. **Finaliser Desktop Mode** — intégrer le fond d'écran officiel, achever le dock LEOS sur Plasma avec sauvegarde et confirmation, puis ajouter les raccourcis globaux KDE.
2. **Finaliser Gaming Mode** — poursuivre les intégrations d'émulateurs et contrôler les profils de manettes ainsi que le comportement sur plusieurs matériels.
3. **Verrouiller le packaging** — vérifier les dépendances de l'image, préparer les éléments publics/privés Cosign et garder les opérations de publication manuelles.
4. **Première image signée** — lancer le workflow uniquement après préparation de la signature et d'une machine de test ; résoudre les éventuelles incompatibilités du build.
5. **Validation matérielle** — tester le premier démarrage, les transitions Desktop/Gaming, la vidéo et l'audio, les manettes, le Bluetooth, le GPU, la boutique, les mises à jour et le rollback.
6. **ISO installable** — choisir et valider le processus ISO après stabilisation de l'image bootable.

## État actuel

- [x] Architecture commune Bazzite KDE / BlueBuild et deux modes au sein d'une seule session.
- [x] Prototypes source du sélecteur, Gaming, Desktop, Centre de contrôle, Centre des manettes, boutique et notifications.
- [x] Imports de bibliothèque Steam, Heroic et Lutris, ajout manuel, favoris, récents et navigation manette.
- [x] Emblèmes officiels et vidéos Desktop/Gaming présents dans le dépôt et copiés dans la recette.
- [x] Transitions vidéo via Qt Multimedia avec piste audio configurable et repli en cas d'erreur.
- [x] Contrôles Python automatisés et validation/génération de la recette BlueBuild réussis sur GitHub Actions.
- [ ] Fond d'écran officiel et intégration complète du dock au véritable panneau Plasma.
- [ ] Intégrations d'émulateurs et validation élargie sur plusieurs configurations matérielles.
- [ ] Ajouter cosign.pub et configurer le secret GitHub SIGNING_SECRET correspondant.
- [ ] Construire une image LEOS signée, puis la tester sur un PC de test Bazzite.
- [ ] Préparer une ISO installable après validation de l'image.

**Aucune image LEOS compilée ni ISO installable n'est encore disponible.** Le workflow de validation Python est en place ; ses résultats devront être consultés sur GitHub Actions.

---

*LEOS — One system. Two experiences.*
