# LEOS — système visuel d’interface

## Intention

LEOS doit évoquer un environnement matériel haut de gamme : calme et précis sur Desktop, immersif sur Gaming, lisible et rassurant dans les outils système. Le néon n'est jamais un décor permanent ; il sert à guider l'œil vers une action, une sélection ou une information importante.

## Palette et surfaces

- Le fond de référence reste presque noir, avec des surfaces distinctes plutôt que des panneaux uniformément gris.
- Les deux accents A/B restent entièrement définis par l'utilisateur. Aucun écran ne réintroduit une palette fixe.
- Le dégradé A→B est réservé aux repères d'identité, aux rails de sélection et aux indicateurs actifs.
- Les halos d'ambiance doivent rester faibles : ils donnent de la profondeur sans concurrencer le contenu.
- Les couleurs sémantiques (erreur, avertissement, succès) conservent leur sens et ne sont pas remplacées par les accents de marque.

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
