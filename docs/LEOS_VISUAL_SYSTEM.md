# LEOS — système visuel d’interface

## Intention

LEOS doit évoquer un environnement matériel haut de gamme : calme et précis sur Desktop, immersif sur Gaming, lisible et rassurant dans les outils système. Le néon n'est jamais un décor permanent ; il sert à guider l'œil vers une action, une sélection ou une information importante.

## Palette et surfaces

- Le fond de référence reste presque noir, avec des surfaces distinctes plutôt que des panneaux uniformément gris.
- Les deux accents A/B restent entièrement définis par l'utilisateur. Aucun écran ne réintroduit une palette fixe.
- Le dégradé A→B est réservé aux repères d'identité, aux rails de sélection et aux indicateurs actifs.
- Les halos d'ambiance doivent rester faibles : ils donnent de la profondeur sans concurrencer le contenu.
- Les couleurs sémantiques (erreur, avertissement, succès) conservent leur sens et ne sont pas remplacées par les accents de marque.

## Modes d’apparence

- **Sombre** : fond graphite profond, surfaces métalliques distinctes et texte clair.
- **Clair** : fond gris très clair, panneaux blancs, surfaces secondaires nuancées et texte anthracite.
- **Automatique** : mode clair de 07:00 à 18:59 et mode sombre de 19:00 à 06:59, selon l’heure locale.
- Les couleurs A et B sont indépendantes de l’apparence et restent inchangées lors du basculement.
- Les interfaces LEOS Desktop, Gaming et Centre de contrôle actualisent leurs palettes sans redémarrage.
- Le schéma de couleurs KDE et les variantes natives du Plasma Style/Aurorae sont produits pour la même apparence. Leur application au bureau KDE reste explicitement déclenchée depuis le Centre de contrôle.
- SDDM et le splash initial restent neutres : le profil utilisateur et son choix d’apparence ne sont pas encore disponibles avant connexion.

## Formes, espacement et profondeur

- Les conteneurs principaux utilisent des rayons de 15 à 18 px ; les éléments internes, de 7 à 12 px.
- Les bordures sont fines et à faible contraste. Le focus clavier/manette reste explicite et plus marqué que le survol.
- Les panneaux gagnent en profondeur par la différence de surface, les filets de lumière et l'alignement, pas par de grosses ombres artificielles.
- Les espacements suivent une progression cohérente de 4, 8, 12, 16, 24 et 32 px.

## Typographie et hiérarchie

- Les titres de section sont courts, les données importantes sont immédiatement repérables, les libellés secondaires restent discrets.
- Les petits titres en capitales utilisent un espacement de lettres mesuré et ne doivent pas être utilisés pour les longues descriptions.
- Les chiffres de performance sont prioritaires sur leurs explications, mais une valeur indisponible est affichée comme telle.

## Application par surface

- **Sélecteur de modes :** deux cartes de même poids, emblème officiel à droite, bénéfices et capacités à gauche.
- **Desktop :** catalogue clair, catégories stables, tuiles d'applications compactes et identifiables.
- **Gaming :** bibliothèque centrée sur les jaquettes, favoris sous forme de puces, plateforme/source lisibles et fiche de jeu dédiée.
- **Centre de contrôle :** cartes de métriques homogènes, accent fin, données réelles uniquement et valeurs manquantes explicites.
- **Notifications :** état non lu visible mais non agressif ; la gravité conserve un repère sémantique distinct.
- **Centre des manettes :** panneau de diagnostic technique, mesures en direct et contrôles à lecture claire.

## Règles d'interaction

- Survol, sélection persistante et focus sont trois états différents.
- Les transitions respectent les préférences d'animation LEOS.
- Les emblèmes et jaquettes disposent de solutions de repli lisibles lorsqu'ils ne sont pas disponibles.
- La navigation clavier et manette ne perd jamais son indicateur de focus.


## Native KDE chrome — refinement pass

The Plasma panel, widget cards, popups and KWin Aurorae frame now use the same
surface hierarchy as the LEOS applications. The outer perimeter is graphite,
not a permanently lit neon outline; a restrained A/B highlight is reserved for
the leading edge and the active state. Window controls use source A for
minimize/maximize/restore, source B for close, and neutral gray for the
gradient midpoint so per-user recolouring remains deterministic.


## Connexion et démarrage

- **SDDM :** carte de connexion graphite, champs explicitement libellés et contrôles argent neutre. La greeter ne force pas la paire A/B avant que le profil utilisateur soit disponible.
- **Splash KDE :** fond graphite neutre, halos métalliques très faibles et progression argent ; les accents A/B restent réservés aux surfaces utilisateur configurées.
- Les contrôles de veille, redémarrage, extinction et choix de session restent séparés et fonctionnels.


## Cohérence de la Boutique et du Centre de contrôle — passe de finition

- Les catégories de la Boutique sont lues depuis le catalogue validé : aucun filtre ne doit dépendre d'une liste QML maintenue séparément.
- Le compteur distingue les résultats visibles du nombre total de fiches ; un état vide doit toujours proposer une sortie simple (effacer les filtres ou changer de catégorie).
- Les états de santé système (critique, attention, normal) utilisent des couleurs sémantiques indépendantes des accents A/B choisis. Les accents de marque restent dédiés à la sélection, à l'identité et aux actions actives.
- La vue d'ensemble du Centre de contrôle résume l'état de santé et permet d'ouvrir le diagnostic détaillé en une action.
- Les raccourcis système Desktop gardent le même focus, le même contraste et les mêmes surfaces que le catalogue LEOS ; les applications KDE absentes doivent produire un retour visible sans fermer le menu.


## Identité commune Desktop / Gaming

- Les deux modes utilisent le composant QML partagé `branding/qml/ModeIdentity.qml` pour présenter l'emblème officiel du mode, le libellé de l'expérience et le même filet A→B.
- Desktop affiche le lion seul avec le libellé `DESKTOP MODE` ; Gaming affiche le lion avec manette et le libellé `GAMING MODE`.
- Les deux hôtes injectent les couleurs A/B réellement choisies par l'utilisateur et les couleurs de texte calculées par le moteur de thème. Aucun accent fixe ne remplace la paire personnelle.
- Le bureau expose un accès explicite `CHANGER DE MODE` vers le sélecteur ; le dock contient déjà le sélecteur par défaut et le mécanisme de migration ajoute ce raccourci sans écraser les favoris existants. Gaming conserve son retour Desktop.
- Le composant partagé complète les fonds et animations officiels dédiés à chaque mode ; il ne les remplace pas.
