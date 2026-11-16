# Premier démarrage de LEOS

## Guide d'accueil

Lors de la première ouverture du sélecteur, LEOS affiche un guide non bloquant qui rappelle :

- Desktop Mode est l'environnement KDE destiné au quotidien.
- Gaming Mode est l'interface plein écran dédiée à la bibliothèque et à la navigation au clavier ou à la manette.
- Les deux modes appartiennent au même système et les applications ouvertes ne sont pas fermées automatiquement lors d'un changement de mode.
- L'utilisateur peut choisir les deux couleurs A et B de l'identité LEOS. Un aperçu montre le dégradé avant de continuer ; les couleurs peuvent aussi être conservées par défaut et modifiées plus tard dans le Centre de contrôle.
- L'utilisateur peut choisir l'apparence sombre (par défaut), claire ou automatique. Le mode automatique utilise l'heure locale : clair de 07:00 à 18:59, sombre de 19:00 à 06:59.
- Les couleurs A-B et l'apparence sont indépendantes : le même dégradé est conservé dans les deux modes, tandis que les surfaces neutres et les couleurs de texte changent pour maintenir le contraste.
- L'apparence sélectionnée s'applique immédiatement aux interfaces LEOS. Le schéma des applications KDE et des éléments Plasma reste un réglage séparé : il peut être appliqué explicitement depuis « Paramètres KDE » dans le Centre de contrôle.

Le bouton **Compris** mémorise que le guide a été lu dans `~/.config/leos/settings.json`, via la préférence `onboarding_complete`. Choisir directement Desktop ou Gaming mémorise également cette étape. Si l'enregistrement échoue, le démarrage continue et le guide pourra réapparaître à la prochaine ouverture.

## Couleurs de l'identité LEOS

Les boutons **A** et **B** ouvrent chacun un sélecteur de couleur. La paire complète est validée et enregistrée en une seule opération dans `~/.config/leos/settings.json` (`theme_color_a` et `theme_color_b`). Le dégradé des composants LEOS se met à jour immédiatement. Les emblèmes, aperçus de fonds et introductions vidéo sont régénérés en arrière-plan dans le cache utilisateur ; les médias officiels restent inchangés et servent de solution de repli si une conversion échoue.

La sélection n'est pas obligatoire : cliquer sur **Compris**, ou choisir directement Desktop/Gaming, permet de conserver les couleurs courantes. Le même réglage A/B reste accessible ensuite dans le Centre de contrôle LEOS.

## Apparence claire, sombre et automatique

La préférence `appearance_mode` est enregistrée dans `~/.config/leos/settings.json` et accepte `dark`, `light` ou `auto`. Le choix sombre est utilisé par défaut. Le mode clair utilise des surfaces blanc cassé et gris doux, avec un texte foncé ; les couleurs A et B restent inchangées.

En mode automatique, les interfaces LEOS basculent sur le thème clair à 07:00 et reviennent au thème sombre à 19:00, selon l'heure locale de l'appareil. Le changement est partagé entre le sélecteur de mode, le bureau LEOS, Gaming Mode, la boutique et les centres de contrôle.

Le thème des applications KDE et des composants natifs Plasma n'est pas forcé au premier démarrage. Pour leur transmettre la palette A-B et l'apparence choisie, l'utilisateur confirme l'action **Appliquer à KDE** dans la section **Paramètres KDE** du Centre de contrôle. En mode automatique, cette application KDE reste manuelle ; la bascule programmée concerne les interfaces LEOS.

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

## Dossier de téléchargement des jeux

Sur un profil neuf, si le dossier de téléchargement XDG pointe encore vers le dossier standard \`~/Downloads\` ou \`~/Téléchargements\`, le service de session LEOS le définit sur \`~/Jeux\`. Un chemin XDG personnalisé est conservé et surveillé à la place. Les fichiers de jeux reconnus sont triés après stabilisation du téléchargement ; les formats ambigus et les archives contenant plusieurs jeux restent dans le dossier d'arrivée pour un choix manuel. LEOS ne télécharge aucun jeu, BIOS, firmware ni clé.

## Ce que LEOS ne fait pas automatiquement

Le premier démarrage ne modifie pas :

- la langue, le fuseau horaire ou les paramètres régionaux déjà choisis dans l'installateur ou KDE ;
- la résolution, la fréquence, l'orientation ou la disposition des écrans ;
- le thème KDE, les panneaux, les widgets, les favoris ou le dock ;
- les applications installées, à moins que l'utilisateur accepte séparément la proposition facultative.

Les réglages avancés restent accessibles dans KDE et le Centre de contrôle LEOS.

## Validation avant publication

- [ ] Le guide apparaît quand `onboarding_complete` est faux.
- [ ] Les sélecteurs A et B affichent les couleurs actuellement enregistrées.
- [ ] Les options Sombre, Clair et Automatique sont disponibles au premier démarrage et dans le Centre de contrôle.
- [ ] Le mode automatique bascule à 07:00 et 19:00 selon l'heure locale.
- [ ] Le changement d'apparence conserve strictement les couleurs A et B et adapte les contrastes des textes.
- [ ] Le schéma KDE/Plasma est appliqué uniquement après confirmation explicite dans le Centre de contrôle.
- [ ] Choisir A ou B met à jour le dégradé partagé et conserve l'autre extrémité.
- [ ] Une paire invalide n'écrase pas les couleurs précédentes.
- [ ] **Compris** masque le guide et mémorise le choix sans imposer une sélection de couleurs.
- [ ] Choisir Desktop ou Gaming mémorise également la lecture du guide.
- [ ] Un problème d'écriture des préférences ne bloque pas le démarrage d'un mode.
- [ ] La proposition d'applications apparaît uniquement après l'entrée dans Desktop.
- [ ] Le dossier XDG standard devient `~/Jeux` sur un profil neuf, sans écraser un dossier de téléchargement personnalisé.
- [ ] Choisir Non n'ajoute pas Flathub et ne lance aucun Flatpak.
- [ ] Choisir Oui installe seulement les applications manquantes après confirmation.
- [ ] Une erreur sur une application n'empêche pas les autres installations ; le parcours reste réessayable sans doublonner les applications déjà présentes.
- [ ] Pendant Gaming Mode, aucune fenêtre d'installation facultative ne s'ouvre.
- [ ] Une réponse déjà mémorisée n'est pas redemandée.
- [ ] L'absence de `kdialog` n'entraîne aucune installation silencieuse.

Le parcours est implémenté dans les sources, mais ces scénarios doivent encore être vérifiés sur une session KDE/Bazzite réelle.
