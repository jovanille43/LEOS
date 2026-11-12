# LEOS Mode Selector — Design retenu

## Décision validée

**Option C : sélecteur hybride.**

Le sélecteur présente les deux expériences au sein d'une seule session KDE. Les introductions cinématiques sont jouées au moment du changement de mode, après l'action de l'utilisateur et les confirmations nécessaires.

## Écran de sélection

- Écran plein format sur fond noir, accents cyan et magenta et typographie LEOS.
- Deux cartes Desktop Mode et Gaming Mode de même taille et de même importance.
- Desktop utilise exclusivement l'emblème officiel du lion seul.
- Gaming utilise exclusivement l'emblème officiel du lion avec manette.
- L'horloge, la date et le dernier mode utilisé sont visibles ; le dernier mode est un rappel, pas un démarrage automatique.
- L'image comparative des deux emblèmes est une référence de conception uniquement et ne devient jamais le logo principal.

## Parcours de transition

1. **Desktop :** le choix lance `desktop-intro.mov`, puis ferme le sélecteur pour révéler le bureau KDE déjà actif.
2. **Entrée Gaming :** une boîte de dialogue indique que les applications ouvertes resteront en arrière-plan. Après confirmation, `gaming-intro.mp4` est joué, puis l'application Gaming plein écran démarre.
3. **Retour Desktop :** une confirmation est demandée dans Gaming. Après validation, `desktop-intro.mov` est joué puis l'application Gaming se ferme.
4. LEOS ne termine jamais automatiquement les autres applications ouvertes.
5. Si Qt Multimedia signale une erreur ou si le lecteur dépasse son délai de sécurité, LEOS termine la transition au lieu de rester bloqué.

## Emblèmes et médias

- `branding/desktop-logo.jpeg` est l'emblème Desktop.
- `branding/gaming-logo.jpeg` est l'emblème Gaming.
- `branding/animations/desktop-intro.mov` accompagne les transitions vers Desktop.
- `branding/animations/gaming-intro.mp4` accompagne chaque entrée dans Gaming.
- `branding/animations/gaming-roar-reference.mp4` reste une référence secondaire ; elle n'est pas jouée automatiquement.
- Les pistes audio sont intégrées aux vidéos. Les préférences LEOS permettent de couper le son sans désactiver les animations, et inversement.

## Interaction

- Manette : stick gauche ou croix directionnelle, A/Croix pour valider, B/Rond pour revenir dans les dialogues.
- Clavier : flèches pour naviguer, Entrée pour valider, Échap pour revenir dans les dialogues.
- Souris : sélection directe sur une carte puis validation.
- Le backend de navigation réutilise les profils LEOS en lecture seule, sans remappage global des périphériques.

## Principes d'expérience

- Les cartes gardent la même importance visuelle ; Desktop reste sobre et Gaming plus énergique.
- Les animations et les sons sont désactivables séparément.
- Le focus clavier/manette reste visible et les libellés demeurent accessibles.
- Aucun arrêt d'application sans choix explicite ; les transitions actuelles conservent les autres applications en arrière-plan.

## État

Le sélecteur, l'horloge, le rappel du dernier mode, la navigation souris/clavier/manette, les confirmations et les transitions vidéo/audio sont raccordés côté code. Les emblèmes JPEG et les trois vidéos sont présents dans `branding/`. La restitution multimédia, la synchronisation et le comportement de session restent à valider sur une vraie session Bazzite KDE.

## Présentation des cartes — validée

- **Desktop Mode :** halo cyan, emblème officiel du lion seul, ambiance sobre et élégante.
- **Gaming Mode :** halo cyan et magenta, emblème officiel du lion avec manette, ambiance plus énergique.
- Aucun des deux modes ne doit sembler secondaire.
