# Architecture du système de thèmes bicolores LEOS

## Décision produit

Chaque thème LEOS est une **paire de deux couleurs d'accent distinctes**. Le joueur choisit un thème lors du premier démarrage ; il peut ensuite le modifier dans Centre de contrôle → Apparence.

Le thème recolore les éléments d'accent de l'identité LEOS :
- les interfaces Desktop, Gaming, sélecteur de modes et centres LEOS ;
- les deux emblèmes officiels (lion seul et lion avec manette) ;
- les halos, dégradés et tracés lumineux des fonds d'écran ;
- les introductions vidéo Desktop et Gaming ;
- les éléments graphiques LEOS qui seront raccordés au catalogue central.

Les formes, la composition, la typographie, les proportions, les animations, les détails métalliques et les couleurs neutres restent inchangés. Les jaquettes de jeux, icônes d'applications tierces et contenus utilisateur ne sont jamais recolorés.

## Modèle de palette

Une palette contient au minimum :
- `accent_primary` : première couleur de la paire ;
- `accent_secondary` : deuxième couleur de la paire ;
- des rôles dérivés de chacune (glow, surface teintée, états atténués) ;
- un rôle de transition pour les dégradés ;
- les tokens neutres (fond, surfaces, bordures et textes).

Les deux accents restent distincts. Les nuances sont calculées à partir de chaque accent, sans réduire la paire à une couleur unique.

Le catalogue `desktop/themes.py` est la source de vérité. Les sélecteurs QML et la validation des préférences consomment ce catalogue ; ajouter un assortiment ne nécessite donc pas de maintenir plusieurs listes indépendantes. Les palettes historiques sont conservées pour compatibilité. **Aucun nouvel assortiment n'est ajouté avant que le joueur ait communiqué les paires voulues.**

## Parcours utilisateur

1. Lors du premier démarrage, le sélecteur présente les thèmes connus et un aperçu des deux couleurs.
2. Le joueur choisit sa paire ; le choix est mémorisé indépendamment du guide d'accueil Desktop/Gaming.
3. Les ressources graphiques légères sont générées dans le cache utilisateur. L'entrée dans Desktop/Gaming attend leur disponibilité, mais pas le traitement vidéo long.
4. Le choix peut être modifié à tout moment depuis Centre de contrôle → Apparence.
5. Les applications LEOS observent les préférences partagées et actualisent leur palette. Le schéma de couleurs KDE reste une opération distincte et explicitement confirmée.

## Pipeline des ressources

### Interfaces QML
Les principales interfaces LEOS consomment la palette partagée via `ThemeManager`. Les accents, focus, sélection et surfaces teintées qui ont été raccordés utilisent des rôles sémantiques communs. Les fonds structurels, bordures neutres et couleurs de statut (erreur/avertissement/état matériel) ne sont pas transformés aveuglément.

La recherche de couleurs restantes doit distinguer les accents codés en dur des neutres et des couleurs fonctionnelles : remplacer toute valeur bleutée arbitrairement risquerait de dégrader le contraste ou de recolorer un statut qui n'est pas un accent.

### Emblèmes PNG
Les PNG transparents officiels restent les sources maîtresses. Le moteur génère des copies dans le cache utilisateur et transforme le dégradé cyan→magenta de façon continue vers la paire sélectionnée : les pixels intermédiaires sont interpolés entre les deux nouveaux accents au lieu d'être affectés brutalement à l'un ou l'autre. Il conserve l'alpha, la progression de luminosité, la chute des halos et les détails métalliques. Le dessin, les positions et la répartition spatiale du dégradé restent ceux de l'original. Les originaux empaquetés ne sont jamais écrasés.

### Fonds d'écran SVG
Les deux SVG 4K officiels sont traités comme des modèles. Le moteur génère une copie recolorée dans le cache et la relie à l'emblème correspondant généré pour la même paire. Le fond sombre, la grille, les ombres et les éléments métalliques restent neutres. Les fichiers SVG source et les PNG originaux restent inchangés.

### Introductions vidéo
Les fichiers MOV/MP4 officiels sont conservés comme sources. Le moteur construit une LUT 3D de résolution 49³ et demande à FFmpeg de réencoder les introductions. La même fonction d'interpolation continue que pour les PNG transforme la progression cyan→magenta vers les deux accents choisis ; elle évite une coupure chromatique au milieu du dégradé. Les niveaux lumineux sont conservés et la piste audio est gardée (encodée en AAC dans les variantes MP4).

Le traitement vidéo s'exécute dans un processus séparé afin de ne pas bloquer le sélecteur ni dépendre de sa durée de vie. Si FFmpeg ou un encodeur compatible n'est pas disponible, si la conversion échoue ou si le cache n'est pas prêt, LEOS garde la vidéo officielle. L'absence de FFmpeg ne doit jamais empêcher la session de démarrer.

**Limite de validation :** le pipeline et ses replis sont couverts par des tests automatisés, mais le rendu des vidéos converties n'a pas encore été inspecté visuellement sur une vraie session Bazzite. Le résultat devra être contrôlé pour le lion, les textes, les couleurs métalliques et la synchronisation audio.

### Icônes et thèmes Plasma
Pour chaque palette non originale, le moteur génère maintenant des copies utilisateur du thème d'icônes LEOS, du Plasma Style et de la décoration Aurorae, dans le cache privé `$XDG_CACHE_HOME/leos/themes/<empreinte>/kde/`. Chaque paquet reçoit un identifiant distinct (`leos-<theme>`) et des métadonnées adaptées. Les SVG de dégradé conservent leurs positions et transitions ; les aplats sombres et contours gris peu saturés restent protégés.

Depuis Centre de contrôle → Apparence, une action confirmée exporte les trois paquets dans l'espace de données utilisateur XDG : `icons/leos-<theme>`, `plasma/desktoptheme/leos-<theme>` et `aurorae/themes/leos-<theme>`. Un identifiant déjà occupé par un contenu différent est refusé ; un paquet identique peut être réexporté sans effet. L'export ne sélectionne aucun thème et ne change aucun réglage Plasma. L'utilisateur choisit ensuite séparément les icônes, le Plasma Style et la décoration Aurorae dans les paramètres KDE. Leur désinstallation automatisée et leur sélection/restauration depuis LEOS restent à implémenter. Le système immuable Bazzite et les sources empaquetées restent intacts.

## Compatibilité et sûreté

- Le système de thème ne dépend pas d'un GPU dédié ni de Vulkan.
- Le cache est utilisateur, avec des écritures temporaires puis remplacement atomique ; les sources officielles restent intactes.
- Un identifiant ou une palette invalide retombe sur le thème de référence.
- La génération graphique légère est asynchrone ; un échec conserve les ressources officielles.
- La vidéo est facultative et possède un repli explicite.
- Les ressources de tiers et les fichiers personnels ne sont jamais recolorés.
- Les contrastes du texte et des états de focus doivent rester lisibles pour chaque future paire.

## État du socle préparé

- [x] Catalogue central de thèmes bicolores et rôles dérivés pour les halos, surfaces teintées et dégradés.
- [x] Persistance du thème et distinction entre choix initial et guide d'accueil.
- [x] Sélection au premier démarrage et sélecteur du Centre de contrôle reliés au même catalogue.
- [x] Gestionnaire partagé qui diffuse la palette entre les applications LEOS.
- [x] Principales interfaces QML raccordées aux deux accents sémantiques.
- [x] Génération en cache des deux emblèmes officiels et des deux fonds SVG recolorés.
- [x] Pipeline vidéo à LUT sélective, traitement séparé et repli vers les sources officielles.
- [x] Tests Python, tests d'assets, lint QML, validation des ressources de marque et recettes BlueBuild réussis sur GitHub Actions pour le commit contrôlé.
- [ ] Ajouter les nouvelles paires lorsque le joueur les aura communiquées.
- [ ] Inspecter le rendu réel des emblèmes et fonds générés, puis des vidéos converties sur Bazzite.
- [x] Générer dans le cache utilisateur des variantes distinctes des icônes LEOS, du Plasma Style et d'Aurorae, sans modifier les sources ni le profil KDE.
- [x] Exporter les trois paquets dans les emplacements XDG utilisateur après confirmation, sans écraser les variantes existantes.
- [ ] Ajouter leur sélection/restauration depuis LEOS, avec mémorisation de l'état KDE précédent et désinstallation explicite des paquets exportés.
- [ ] Valider le changement à chaud, la persistance, les contrastes et le repli sur des sessions Bazzite réelles et plusieurs résolutions.

Les validations GitHub Actions confirment les contrôles automatisés du code et des recettes ; elles ne remplacent pas l'essai du bureau et des animations sur du matériel réel.

## Critères d'acceptation finaux

1. Chaque paire du catalogue possède deux accents distincts et des nuances lisibles.
2. Un seul choix pilote toutes les applications LEOS raccordées, sans liste de thèmes dupliquée.
3. Les logos, halos, dégradés et fonds d'écran gardent leur géométrie et leurs détails neutres.
4. Les vidéos converties gardent leur piste audio ; un problème de codec revient aux fichiers officiels sans bloquer LEOS.
5. Les changements de palette ne recolorent ni jaquettes, ni icônes tierces, ni statuts fonctionnels.
6. Les thèmes KDE additionnels, s'ils sont intégrés, sont appliqués proprement au profil utilisateur et peuvent être restaurés.
