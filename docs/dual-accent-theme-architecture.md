# Architecture du système de thèmes bicolores LEOS

## Décision produit

Chaque thème LEOS est une **paire de deux couleurs d'accent distinctes**. Le joueur choisit un thème lors du premier démarrage ; il peut ensuite le modifier dans le Centre de contrôle.

Le thème choisi recolore toute l'identité visuelle LEOS :
- interfaces Desktop, Gaming, sélecteur de modes et centres de contrôle ;
- emblèmes officiels Desktop et Gaming ;
- halos, dégradés, tracés lumineux et fonds d'écran ;
- introductions vidéo Desktop et Gaming et leurs effets colorés ;
- icônes et éléments graphiques appartenant à LEOS.

Le thème ne modifie ni la géométrie, ni la composition, ni la typographie, ni les animations, ni les détails métalliques des emblèmes. Le fond sombre et les couleurs neutres restent des éléments structurels, pas des accents à remplacer.

## Modèle de palette

Une palette expose au minimum :
- `accent_primary` : première couleur d'accent ;
- `accent_secondary` : seconde couleur d'accent ;
- des nuances dérivées de chacune (halo, glow, contour, surface teintée et états atténués) ;
- les tokens neutres indépendants des accents (fond, surfaces, bordures, texte).

Les dégradés utilisent les deux couleurs de la paire. Les variantes lumineuses et atténuées sont calculées à partir de chacune ; il ne faut pas réduire les deux accents à une couleur principale unique.

Le thème par défaut conserve la paire historique cyan + magenta pour assurer la continuité visuelle des installations existantes. Les identifiants de thèmes sont stables et les préférences enregistrent l'identifiant, pas des valeurs QML dispersées.

## Parcours utilisateur

1. Au premier démarrage uniquement, proposer une sélection visuelle des thèmes avant l'entrée dans Desktop ou Gaming.
2. Afficher les deux couleurs de chaque paire, avec un aperçu fidèle des halos et dégradés LEOS.
3. Enregistrer le choix dans les paramètres utilisateur. En cas d'échec d'écriture, conserver le thème par défaut et ne jamais bloquer le démarrage.
4. Permettre de changer de thème à tout moment depuis Centre de contrôle → Apparence.
5. Appliquer le changement à tous les composants LEOS sans modifier silencieusement les préférences KDE indépendantes. L'application du schéma de couleurs KDE reste une action explicite si elle est nécessaire.

## Pipeline des ressources

### Interfaces QML et schéma KDE
Les interfaces consomment une seule palette exposée par le contrôleur LEOS. Les références de couleurs cyan/magenta codées en dur doivent être remplacées par des rôles sémantiques (accent primaire, accent secondaire, halo primaire, halo secondaire, dégradé, sélection). Les états de focus et les contrastes doivent rester accessibles.

### Fonds d'écran SVG
Les SVG doivent devenir des modèles utilisant des rôles de couleur explicites. À la sélection d'un thème, LEOS génère des copies utilisateur à partir des modèles et remplace uniquement les couleurs d'accent. Les originaux empaquetés restent immuables. Le fond noir, la grille, les ombres et les tons métalliques restent neutres.

### Emblèmes
Les PNG transparents existants restent les sources officielles. Une étape de recoloration doit cibler uniquement les pixels d'accent cyan/magenta, préserver alpha, luminance, reflets métalliques et contours, puis produire des copies dérivées propres à l'utilisateur ou au cache LEOS. Ne jamais écraser les sources du dépôt.

### Animations vidéo
Les fichiers MOV/MP4 officiels restent les sources maîtresses et leur piste audio doit être conservée. Le pipeline doit recolorer uniquement les zones d'accent des images vidéo en préservant les détails neutres et les effets lumineux. Évaluer un traitement de trames compatible avec Qt Multimedia ou une génération de variantes dérivées à partir des sources ; ne pas appliquer un simple filtre global de teinte qui dénaturerait le lion, les textes ou les éléments métalliques. Prévoir un repli sûr vers la vidéo originale si le traitement n'est pas disponible ou échoue.

### Autres ressources
Les icônes, illustrations et éléments graphiques LEOS doivent déclarer leurs rôles d'accent. Les ressources de tiers, les jaquettes de jeux et les contenus utilisateur ne doivent jamais être recolorés.

## Compatibilité et sûreté

- Le moteur doit fonctionner sans GPU dédié et sans dépendre d'une fonction Vulkan facultative.
- La sélection du thème ne doit jamais empêcher l'ouverture d'une session KDE ou le démarrage de LEOS.
- Le changement de thème doit être atomique : une génération incomplète ne remplace pas les dernières ressources valides.
- Les ressources générées sont stockées dans l'espace utilisateur LEOS, sans modification des fichiers système immuables de Bazzite.
- Les ressources originales et leurs empreintes restent vérifiables.
- Une palette invalide ou un identifiant inconnu retombe sur le thème par défaut.
- Les fonctions d'accessibilité et les contrastes doivent être testés pour chaque palette.

## État observé dans le dépôt au moment de cette décision

- Le catalogue de thèmes comporte désormais les rôles sémantiques bicolores et est partagé entre les applications LEOS.
- Les interfaces QML principales et les ressources PNG/SVG prises en charge disposent d'un chemin de recoloration.
- Les fichiers vidéo restent des sources maîtresses non recolorées ; leur traitement reste explicitement séparé.
- Le choix de thème au premier démarrage est distinct du guide d'accueil.

## Socle technique préparé

Le socle commun est maintenant présent dans la branche de travail :

- `desktop/themes.py` est le catalogue unique des thèmes et expose les deux accents, les noms de présentation et les rôles dérivés (glows, surfaces atténuées et milieu de dégradé). Les nouveaux assortiments seront ajoutés à ce catalogue ; les listes de l'interface et la validation des paramètres le consomment automatiquement.
- Le thème sélectionné est mémorisé dans les paramètres utilisateur. `theme_selection_complete` distingue le choix initial du guide d'accueil Desktop/Gaming.
- Le sélecteur propose les thèmes disponibles au premier démarrage et le Centre de contrôle utilise le même catalogue pour les changements ultérieurs.
- `desktop/theme_manager.py` diffuse les palettes vers les fenêtres QML indépendantes et observe les changements effectués par une autre application LEOS.
- Les écrans Mode Selector, Gaming, Desktop Menu, Notifications, Centre des manettes, Boutique et Centre de contrôle consomment désormais les accents sémantiques au lieu de déclarer chacun leur paire cyan/magenta.
- `desktop/theme_assets.py` prépare des copies PNG des emblèmes officiels et des copies SVG des fonds d'écran dans le cache utilisateur. Le remappage cible les teintes accent cyan/magenta, conserve alpha, saturation relative et luminosité, et laisse les gris métalliques ainsi que les tons neutres intacts. Les fichiers sources du dépôt restent inchangés.
- Les introductions MOV/MP4 passent maintenant par le manifeste commun des ressources. **Elles utilisent encore les vidéos originales** : la transformation des images vidéo n'est pas incluse dans ce socle. Elle reste une étape dédiée, car un simple filtre de teinte risque de recolorer le lion métallique, les textes et les détails neutres.
- Aucun nouvel assortiment de couleurs n'a été inventé dans cette étape. Les palettes déjà présentes sont conservées pour compatibilité ; les prochains assortiments seront ajoutés lorsque les deux couleurs de chaque paire auront été validées.

## Points restant à réaliser

1. Ajouter les nouveaux assortiments communiqués par le joueur, avec contrôles de contraste pour chaque paire.
2. Finaliser et brancher la recoloration des vidéos (avec conservation de la piste audio), puis valider le rendu des introductions sur Bazzite.
3. Étendre la génération aux éventuels éléments SVG/Plasma restants et vérifier qu'aucun accent fixe ne subsiste dans les ressources de marque concernées.
4. Exécuter les tests automatisés, puis valider le rendu sur une vraie session Bazzite et plusieurs GPU/résolutions.

## Plan de réalisation et critères d'acceptation

1. Ajouter les assortiments choisis au catalogue et compléter les tests de contraste.
2. Finaliser le traitement vidéo et la recoloration des ressources Plasma restantes.
3. Vérifier par recherche automatisée qu'aucun accent cyan/magenta fixe ne subsiste hors sources maîtresses, tests de référence et thème historique.
4. Exécuter les tests automatisés, puis valider le rendu sur une vraie session Bazzite et plusieurs GPU/résolutions.

**Le système ne sera considéré comme terminé que lorsque les logos et les animations auront été recolorés eux aussi.** Un changement de couleur limité aux composants QML ne satisfait pas la décision produit.
