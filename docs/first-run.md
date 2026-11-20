# Premier démarrage de LEOS

## Guide d'accueil

Lors de la première ouverture du sélecteur, LEOS affiche un guide non bloquant qui rappelle :

- Desktop Mode est l'environnement KDE destiné au quotidien.
- Gaming Mode est l'interface plein écran dédiée à la bibliothèque et à la navigation au clavier ou à la manette.
- Les deux modes appartiennent au même système et les applications ouvertes ne sont pas fermées automatiquement lors d'un changement de mode.
- Le guide ne change aucun thème, panneau, fond d'écran, réglage KDE ou logiciel.

Le bouton **Compris** mémorise que le guide a été lu dans `~/.config/leos/settings.json`, via la préférence `onboarding_complete`. Choisir directement Desktop ou Gaming mémorise également cette étape.

## Activation visuelle de Desktop

Lors du premier choix de **Desktop Mode**, le sélecteur propose séparément d'activer le profil visuel LEOS ou de garder le bureau KDE actuel.

- Le choix **Activer l'apparence LEOS** vérifie la présence des outils et ressources, inspecte la disposition Plasma et refuse les configurations multi-panneaux ou non inspectables.
- Avant toute modification du panneau ou du fond d'écran, LEOS crée une sauvegarde vérifiée de `plasma-org.kde.plasma.desktop-appletsrc`.
- Après confirmation, LEOS applique le schéma couleur **LEOS Original**, le Plasma Style **LEOS**, le thème d'icônes **LEOS**, le fond officiel Desktop et le dock inférieur centré avec les applications disponibles.
- Les gestionnaires de couleurs et de style conservent chacun le thème précédent pour restauration. Si une étape échoue, LEOS tente de restaurer la disposition, le style et les couleurs précédents ; le choix reste en attente pour permettre une nouvelle tentative.
- Le choix **Garder mon bureau actuel** enregistre `desktop_appearance_setup=skipped` et ne modifie aucun réglage KDE. Le Centre de contrôle reste disponible pour une personnalisation ultérieure.
- Une application réussie enregistre `desktop_appearance_setup=applied`.

Le rendu réel du fond d'écran, du Plasma Style et du dock, ainsi que le retour arrière, doivent encore être validés dans une installation Bazzite KDE complète en machine virtuelle.

## Applications facultatives

Après une sélection réussie de **Desktop Mode**, le lanceur peut ouvrir une proposition séparée pour Brave, LibreOffice et VLC.

- Une réponse positive autorise l'ajout du dépôt utilisateur Flathub et l'installation des seules applications absentes.
- Les applications déjà présentes dans l'installation utilisateur ou système sont ignorées.
- Flathub n'est ajouté au profil utilisateur que si au moins une des applications approuvées manque ; si elles sont toutes déjà installées, aucune modification de dépôt n'est effectuée.
- Avant toute installation, l'URL du dépôt utilisateur nommé `flathub` est comparée aux adresses HTTPS canoniques officielles. Si le nom existe mais pointe ailleurs, l'installation est bloquée ; le consentement reste conservé pour permettre une reprise après correction manuelle du dépôt.
- Le consentement positif est enregistré avant toute installation dans `~/.local/state/leos/default-apps-consent-v1` (ou sous `$XDG_STATE_HOME` si cette variable est définie). Cette autorisation concerne uniquement la liste versionnée Brave, LibreOffice et VLC.
- Si une installation échoue, les autres applications sont tout de même traitées. Le consentement est conservé et une prochaine entrée dans Desktop reprend uniquement les applications manquantes, sans afficher une seconde demande d'autorisation.
- Lorsque toutes les applications sont déjà présentes ou ont été installées, LEOS enregistre `default-apps-seeded` puis supprime le marqueur temporaire de consentement.
- Une réponse négative n'ajoute pas Flathub, ne lance aucune installation et enregistre directement `default-apps-seeded` pour ne pas reposer la question à chaque session.
- Une erreur technique de `kdialog` n'est pas traitée comme un refus : aucun marqueur de décision n'est écrit et le lanceur pourra réessayer.
- La proposition n'est pas lancée pendant Gaming Mode. Elle sera présentée lors d'une prochaine entrée dans Desktop si aucune réponse n'a encore été mémorisée.
- Sans `kdialog`, aucune installation n'est effectuée ; le lanceur pourra réessayer lors d'une prochaine entrée dans Desktop.
- Les applications restent ensuite gérables depuis la boutique LEOS. Une désinstallation volontaire n'entraîne pas de réinstallation automatique.

Aucun service indépendant ne présente une seconde fenêtre de bienvenue au démarrage de session. Le lanceur orchestre le parcours après le choix de mode.

## Ce que LEOS ne fait pas automatiquement

En l'absence de consentement pour le profil visuel LEOS, le premier démarrage ne modifie pas :

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
