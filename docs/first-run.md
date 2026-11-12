# Premier démarrage de LEOS

## Guide d'accueil

Lors de la première ouverture du sélecteur, LEOS affiche un guide non bloquant qui rappelle :

- Desktop Mode est l'environnement KDE destiné au quotidien.
- Gaming Mode est l'interface plein écran dédiée à la bibliothèque et à la navigation au clavier ou à la manette.
- Les deux modes appartiennent au même système et les applications ouvertes ne sont pas fermées automatiquement lors d'un changement de mode.
- Le guide ne change aucun thème, panneau, fond d'écran, réglage KDE ou logiciel.

Le bouton **Compris** mémorise que le guide a été lu dans `~/.config/leos/settings.json`, via la préférence `onboarding_complete`. Choisir directement Desktop ou Gaming mémorise également cette étape. Si l'enregistrement échoue, le démarrage continue et le guide pourra réapparaître à la prochaine ouverture.

## Applications facultatives

Après une sélection réussie de **Desktop Mode**, le lanceur peut ouvrir une proposition séparée pour Brave, LibreOffice et VLC.

- Une réponse positive autorise l'ajout du dépôt utilisateur Flathub et l'installation des seules applications absentes.
- Les applications déjà présentes dans l'installation utilisateur ou système sont ignorées.
- Si une installation échoue, les autres applications sont tout de même traitées. Le parcours reste en attente et pourra être retenté lors d'une prochaine entrée dans Desktop ; les applications déjà installées seront ignorées.
- Une réponse négative n'ajoute pas Flathub et ne lance aucune installation.
- La réponse est mémorisée dans `~/.local/state/leos/default-apps-seeded` (ou sous `$XDG_STATE_HOME` si cette variable est définie).
- La proposition n'est pas lancée pendant Gaming Mode. Elle sera présentée lors d'une prochaine entrée dans Desktop si aucune réponse n'a encore été mémorisée.
- Sans `kdialog`, aucune installation n'est effectuée ; le lanceur pourra réessayer lors d'une prochaine entrée dans Desktop.
- Les applications restent ensuite gérables depuis la boutique LEOS. Une désinstallation volontaire n'entraîne pas de réinstallation automatique.

Aucun service indépendant ne présente une seconde fenêtre de bienvenue au démarrage de session. Le lanceur orchestre le parcours après le choix de mode.

## Ce que LEOS ne fait pas automatiquement

Le premier démarrage ne modifie pas :

- la langue, le fuseau horaire ou les paramètres régionaux déjà choisis dans l'installateur ou KDE ;
- la résolution, la fréquence, l'orientation ou la disposition des écrans ;
- le thème KDE, les panneaux, les widgets, les favoris ou le dock ;
- les applications installées, à moins que l'utilisateur accepte séparément la proposition facultative.

Les réglages avancés restent accessibles dans KDE et le Centre de contrôle LEOS.

## Validation avant publication

- [ ] Le guide apparaît quand `onboarding_complete` est faux.
- [ ] **Compris** masque le guide et mémorise le choix.
- [ ] Choisir Desktop ou Gaming mémorise également la lecture du guide.
- [ ] Un problème d'écriture des préférences ne bloque pas le démarrage d'un mode.
- [ ] La proposition d'applications apparaît uniquement après l'entrée dans Desktop.
- [ ] Choisir Non n'ajoute pas Flathub et ne lance aucun Flatpak.
- [ ] Choisir Oui installe seulement les applications manquantes après confirmation.
- [ ] Une erreur sur une application n'empêche pas les autres installations ; le parcours reste réessayable sans doublonner les applications déjà présentes.
- [ ] Pendant Gaming Mode, aucune fenêtre d'installation facultative ne s'ouvre.
- [ ] Une réponse déjà mémorisée n'est pas redemandée.
- [ ] L'absence de `kdialog` n'entraîne aucune installation silencieuse.

Le parcours est implémenté dans les sources, mais ces scénarios doivent encore être vérifiés sur une session KDE/Bazzite réelle.
