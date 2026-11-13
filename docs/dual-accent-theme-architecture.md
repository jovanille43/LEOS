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

- `desktop/themes.py` possède déjà deux tokens d'accent, mais les thèmes existants sont encore organisés autour des variantes historiques Original, Light, Cyan, Magenta et Gaming.
- Le Centre de contrôle expose une palette aux composants QML ; plusieurs interfaces et ressources de marque conservent toutefois des valeurs cyan/magenta littérales.
- Les fonds d'écran SVG contiennent directement leurs couleurs d'accent.
- Les emblèmes officiels sont des PNG transparents statiques.
- Les introductions Desktop et Gaming sont des fichiers vidéo MOV/MP4 statiques.
- Le premier démarrage actuel présente un guide d'accueil, mais ne propose pas encore le choix de palette.

## Plan de réalisation et critères d'acceptation

1. Étendre le modèle de palette bicolore et centraliser les rôles sémantiques ; ajouter les tests de validation et de contraste.
2. Ajouter la sélection au premier démarrage, la persistance du choix et le réglage dans le Centre de contrôle.
3. Migrer toutes les interfaces QML et les schémas KDE vers les deux accents sémantiques.
4. Rendre les fonds SVG générables depuis une paire de couleurs.
5. Développer et tester la recoloration ciblée des emblèmes.
6. Définir puis valider le traitement des introductions vidéo sans altérer les détails neutres ni l'audio.
7. Vérifier par recherche automatisée qu'aucun accent cyan/magenta historique ne reste dans les ressources LEOS, sauf sources maîtresses, tests de référence et thème historique.
8. Exécuter les tests automatisés, puis valider le rendu sur une vraie session Bazzite et plusieurs GPU/résolutions.

**Le système ne sera considéré comme terminé que lorsque les logos et les animations auront été recolorés eux aussi.** Un changement de couleur limité aux composants QML ne satisfait pas la décision produit.
