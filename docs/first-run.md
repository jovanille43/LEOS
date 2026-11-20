# Premier démarrage de LEOS

## Choix obligatoire de l'identité A/B

À la toute première ouverture, avant que Desktop ou Gaming puisse être lancé, le sélecteur ouvre un écran LEOS de choix des couleurs. L'utilisateur choisit séparément A et B ; aucune palette cyan/magenta historique n'est proposée ni appliquée par défaut. Les tons métalliques visibles avant ce choix sont de simples repères neutres. La validation enregistre la paire dans les paramètres LEOS, puis le même dégradé est transmis aux interfaces et aux ressources graphiques qui peuvent être recolorées. Si une couleur manque ou si l'enregistrement échoue, le sélecteur reste ouvert et aucun mode n'est lancé.

Les couleurs source présentes dans les anciennes ressources graphiques sont conservées uniquement pour calculer la transformation des visuels ; elles ne sont pas exposées comme palette de l'utilisateur.

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
- Après confirmation, LEOS génère puis applique le schéma de couleurs, le Plasma Style, les icônes et le fond Desktop à partir de la paire A/B choisie, puis configure le dock inférieur centré avec les applications disponibles.
- Les gestionnaires de couleurs et de style conservent chacun le thème précédent pour restauration. Si une étape échoue, LEOS tente de restaurer la disposition, le style et les couleurs précédents ; le choix reste en attente pour permettre une nouvelle tentative.
- Le choix **Garder mon bureau actuel** enregistre `desktop_appearance_setup=skipped` et ne modifie aucun réglage KDE. Le Centre de contrôle reste disponible pour une personnalisation ultérieure.
- Une application réussie enregistre `desktop_appearance_setup=applied`.
- Si l'utilisateur choisit Gaming en premier, le retour vers Desktop rouvre le sélecteur tant que l'apparence est `pending`, afin de présenter le même choix visuel avant de révéler le bureau.

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

### Identité et couleurs A/B

- [ ] L'écran d'identité apparaît avant tout accès à Desktop ou Gaming lors d'un premier démarrage.
- [ ] A et B sont choisies indépendamment ; les deux peuvent être identiques si l'utilisateur le souhaite.
- [ ] Les valeurs exactes choisies sont enregistrées et restaurées après fermeture puis réouverture de session.
- [ ] Une paire incomplète ou une erreur d'écriture ne permet pas de contourner le choix obligatoire.
- [ ] Aucun ancien cyan/magenta n'apparaît comme accent par défaut.
- [ ] Les logos, fonds et introductions recolorés utilisent la paire choisie sans teinter les gris métalliques.
- [ ] Si la génération d'un visuel échoue (codec, fichier absent ou cache), le sélecteur reste utilisable et aucun visuel source non recoloré ne remplace l'identité choisie.

### Apparence Desktop et retour arrière

- [ ] **Activer l'apparence LEOS** demande confirmation et crée une sauvegarde Plasma vérifiée avant toute modification.
- [ ] Le profil applique le fond Desktop, le schéma de couleurs, le Plasma Style, les icônes et le dock lorsque les composants requis sont disponibles.
- [ ] Une disposition multi-panneaux ou non inspectable est refusée sans changement de configuration.
- [ ] Une erreur pendant l'application restaure les réglages précédents et laisse la configuration en attente pour une nouvelle tentative.
- [ ] **Garder mon bureau actuel** ne modifie ni le fond d'écran, ni le thème, ni les panneaux.
- [ ] Après application réussie, le profil ne se réapplique pas à chaque session et l'utilisateur conserve l'accès aux paramètres KDE natifs.

### Guide et applications facultatives

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

## Identité système avant et après connexion

L'image intègre un thème Plymouth LEOS, un écran de connexion SDDM Qt 6 et un splash Plasma post-connexion. Ces trois écrans utilisent une base sombre et métallique neutre, car les couleurs A/B de l'utilisateur ne sont pas connues avant sa connexion. Noto Sans est la typographie commune à ces interfaces.

Le thème de curseur LEOS fournit une première forme SVG recolorable avec les couleurs A/B ; les formes non fournies héritent de Breeze. Les décorations Aurorae des fenêtres sont également générées dans une variante utilisateur avec cette paire. Après consentement à l'application de l'apparence Desktop, le splash, le curseur, le décor des fenêtres et le fond du verrouillage sont configurés dans le compte utilisateur. Les valeurs précédentes sont sauvegardées et peuvent être restaurées. Les changements de splash, de curseur, de décor et de fond de verrouillage sont appliqués via les réglages natifs KDE et peuvent nécessiter une réouverture de session.

La présence des ressources dans l'image et le passage de la CI ne remplacent pas les essais visuels sur une image réellement démarrée : UEFI, écrans haute résolution, multi-écrans, reprise après veille et restauration des paramètres doivent encore être vérifiés.

Dans le Centre de contrôle, l'action « Appliquer le style LEOS » actualise le Plasma Style, les icônes, le décor Aurorae, le splash Plasma, le curseur et le fond du verrouillage à partir de la même paire A/B. « Restaurer le style précédent » restaure l'ensemble des valeurs précédentes. Si l'utilisateur a modifié manuellement une de ces valeurs après l'application LEOS, la restauration refuse de l'écraser et signale le conflit.

Le même fond A/B est configuré pour l'écran de verrouillage KDE via `kscreenlockerrc` (`Greeter/Wallpaper/org.kde.image/General/Image` et `PreviewImage`). Ce réglage est sauvegardé avec le splash, le curseur et le décor Aurorae. Le dialogue de saisie du mot de passe reste le composant natif sécurisé de KDE : LEOS ne le remplace pas.
