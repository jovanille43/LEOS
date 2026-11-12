# LEOS Control Center

Premier panneau de préférences LEOS réalisé avec Qt 6 / QML et PySide6.

## Préférences actuellement persistées

- Thème sélectionné (LEOS Original, Light, Cyan, Magenta, Gaming).
- Animations et sons LEOS activés/désactivés.
- Overlay Gaming activé/désactivé.
- Profil de performances sélectionné.

Les valeurs sont conservées dans `~/.config/leos/settings.json` (ou `$XDG_CONFIG_HOME/leos/settings.json`) et protégées par des permissions utilisateur.

## Limites

Le panneau enregistre les préférences, mais tous les moteurs d'application visuelle/sonore et de gestion des performances ne sont pas encore intégrés. La sélection d'un profil ne change pas encore les fréquences CPU/GPU. Les paramètres système avancés restent ouverts dans KDE System Settings.

Le prototype n'a pas encore été exécuté dans une session Bazzite/KDE.


## Vérification des mises à jour système

Le Centre de contrôle peut lancer `uupd update-check` via `pkexec` (uniquement pour vérifier si une mise à jour d'image existe). Les codes retour de uupd sont interprétés sans déclencher l'installation : 0 signifie qu'une mise à jour est disponible, 77 que l'image est à jour. Quand `bazzite-updater` est présent sur l'image, le bouton dédié ouvre son interface pour que l'utilisateur consulte les détails et choisisse l'installation.

Aucune commande d'installation, de déploiement ou de redémarrage n'est appelée par cette page. Le timer automatique livré par Bazzite et la politique rpm-ostree de l'image de base ne sont pas modifiés à ce stade. Cette intégration ne désactive pas les mécanismes automatiques hérités de Bazzite. Sur les images Desktop, Bazzite vérifie quotidiennement les mises à jour et peut préparer un déploiement en arrière-plan lorsque la machine est inactive. LEOS observe ensuite, toutes les dix minutes pendant que le Centre de contrôle est ouvert, l’état local en lecture seule (`rpm-ostree status --json`). Lorsqu’un déploiement est effectivement préparé, LEOS affiche son état et envoie une notification unique par identifiant de déploiement. LEOS ne lance pas lui-même la recherche réseau ni le téléchargement en arrière-plan.

## Mises à jour système

La page **Mises à jour** est accessible dans la navigation latérale. La vérification utilise exclusivement la commande en lecture seule `uupd update-check`, via `pkexec` pour les sessions non privilégiées. Elle n'installe pas de mise à jour. Lorsque l'outil officiel `bazzite-updater` est présent, le bouton dédié l'ouvre afin que l'utilisateur consulte les changements et décide lui-même de l'installation.

Les résultats sont affichés dans la page et les événements importants sont enregistrés dans l'historique de notifications LEOS. La disponibilité de l'outil est détectée à l'exécution ; aucun exécutable factice n'est fourni. La vérification réseau est limitée à deux minutes ; l'observation locale d'un déploiement en attente est limitée à vingt secondes. En cas de dépassement, LEOS interrompt uniquement la commande de lecture concernée, affiche un avertissement et permet de réessayer. Ces délais ne coupent jamais une installation système, qui reste du ressort de Bazzite.

**Validation restante :** exécuter la vérification dans une image Bazzite réelle et confirmer la disponibilité des commandes sur les variantes d'image ciblées. Le projet ne modifie pas les timers ni les politiques de mise à jour Bazzite.


Le suivi périodique se limite à l’observation des déploiements en attente, via l’API JSON locale de rpm-ostree. Il n’interroge pas le réseau et ne lance aucune transaction. Le contrôle périodique fonctionne lorsque le Centre de contrôle est ouvert ; les vérifications et opérations automatiques de Bazzite restent gérées par les services natifs du système.

## Préférences de notifications

La page **Notifications** du Centre de contrôle permet d'activer/désactiver les fenêtres système, de choisir une durée de 3, 5 ou 8 secondes, de filtrer les notifications par priorité, de couper leur son via l'indication standard `suppress-sound` et d'activer le silence automatique en Gaming Mode. Les événements continuent d'être enregistrés dans l'historique local même lorsqu'une fenêtre est filtrée ou désactivée.

Les sons reposent sur le service de notifications KDE et sa configuration sonore : LEOS ne joue pas encore de fichier audio propriétaire. Le mode silencieux en jeu est activé par défaut. Les préférences sont stockées dans le fichier utilisateur `settings.json`.
En Gaming Mode, un bouton permanent dans la barre supérieure permet de basculer immédiatement le mode silencieux. L’état est partagé avec le Centre de contrôle et persiste après fermeture du mode Gaming. À l’entrée dans Gaming Mode, LEOS enregistre le mode actif ; le retour au bureau restaure l’état Desktop.
Les préférences partagées sont relues depuis le fichier utilisateur par les processus LEOS. Le Centre de contrôle détecte les changements effectués par Gaming Mode et les autres composants toutes les 1,5 secondes, sans redémarrage de l’interface.


## Inventaire matériel et périphériques

La page **Matériel & connexions** affiche un inventaire en lecture seule : modèle CPU et threads logiques, mémoire disponible/utilisée, occupation du système de fichiers racine, GPU et pilote lorsqu'ils sont exposés par sysfs, distribution, noyau, état Bluetooth et appareils connectés, serveur audio, sortie/entrées audio et contrôleurs de jeu reconnus dans la liste des périphériques Linux.

Les informations sont actualisées à l'ouverture du Centre de contrôle puis toutes les dix secondes, avec un bouton de rafraîchissement manuel. Les sondes utilisent les interfaces locales Linux (/proc, /sys), `pactl`, `bluetoothctl` et `systemctl` lorsqu'ils sont disponibles. Les appels externes sont bornés par un délai maximal et les outils absents ou les autorisations insuffisantes affichent un état indisponible plutôt qu'une valeur inventée.

Cette page ne modifie ni les appareils, ni les pilotes, ni la configuration Bluetooth/audio. Les cartes de raccourci ouvrent les modules natifs KDE pour toute action de configuration. La détection des manettes dépend des noms exposés dans `/proc/bus/input/devices` et peut ne pas identifier certains modèles ; l'état de batterie et les fonctions avancées par contrôleur restent à intégrer.

**Validation restante :** les tests automatisés couvrent les réponses disponibles/indisponibles et les délais d'expiration. La détection réelle doit encore être vérifiée sur différentes machines Bazzite, notamment avec GPU hybrides, périphériques Bluetooth et PipeWire.

L'inventaire inclut également le niveau et l'état de la batterie lorsque le noyau expose une alimentation de type batterie, ainsi que les périphériques USB dont les noms fabricant/produit sont publiés dans sysfs. Les machines fixes affichent explicitement qu'aucune batterie n'a été détectée.

Le tableau inclut enfin les interfaces réseau locales et leurs adresses IPv4/IPv6 à partir de `ip -brief address`. L'interface de boucle locale est masquée ; aucun service distant ni test de débit n'est lancé par cette détection.


## Diagnostic système

La page **Diagnostic système** fournit un bilan en lecture seule actualisé toutes les 30 secondes, avec analyse manuelle à la demande. Elle contrôle l'occupation du système de fichiers racine, la mémoire disponible, les températures publiées par les zones thermiques du noyau, les unités systemd en échec, la charge moyenne, le temps de fonctionnement et le nombre d'entrées d'erreur récentes du journal système.

Les seuils d'attention sont explicites : stockage à partir de 80 % (critique à 90 %), mémoire à partir de 85 % (critique à 92 %) et température exposée à partir de 80 °C (critique à 90 °C). La température affichée est le maximum des capteurs accessibles, pas une mesure garantie du CPU seul. Les journaux ne sont jamais reproduits dans l'interface ; seule une quantité d'entrées est indiquée. Les sondes sont bornées dans le temps et s'exécutent hors du thread graphique pour préserver la réactivité du Centre de contrôle.

Le diagnostic ne lance aucune réparation, aucun redémarrage de service, aucune suppression et aucune modification de configuration. Les résultats peuvent être partiels si systemd, journalctl, les capteurs ou les permissions ne sont pas disponibles. Une anomalie signalée est une piste à examiner, pas une preuve de panne matérielle.

La page affiche également les huit processus les plus consommateurs en CPU, avec PID, mémoire résidente et pourcentages CPU/RAM, à partir de `ps`. Cette liste est informative et en lecture seule : LEOS ne termine aucun processus automatiquement.

Un raccourci ouvre également **Moniteur système KDE** lorsqu'il est présent, sans élévation de privilèges. Il sert d'outil natif pour approfondir l'inspection ou gérer manuellement les processus ; LEOS ne termine aucun processus depuis son propre diagnostic.


## Centre de nettoyage (prévisualisation)

La page **Nettoyage** inspecte uniquement le cache de miniatures KDE (`~/.cache/thumbnails`) et les fichiers déjà placés dans la corbeille utilisateur (`~/.local/share/Trash/files`). Elle affiche le nombre de fichiers et l'espace occupé, actualisés à la demande ou toutes les 60 secondes. Les liens symboliques ne sont pas suivis ; les erreurs d'accès sont ignorées sans interrompre l'analyse.

Cette première version est strictement en prévisualisation : aucun fichier n'est déplacé, vidé ou supprimé. Elle exclut volontairement le cache global des applications, les données personnelles, les journaux système et les composants immuables de Bazzite. La stratégie d'action (mise à la corbeille ou suppression définitive, avec confirmation explicite et aperçu exact des éléments) reste à définir avant d'activer toute opération destructive.


## Tableau réseau

La page **Réseau** présente l'état des interfaces, l'interface portant la route par défaut, la passerelle IPv4, les serveurs DNS configurés, ainsi que le SSID et le niveau radio Wi-Fi lorsque `iw` expose ces informations. Les débits entrants et sortants sont calculés à partir des compteurs d'octets locaux de sysfs entre deux relevés espacés de trois secondes.

Le relevé s'exécute hors du thread graphique, sans générer de trafic de test et sans modifier NetworkManager, les routes, le DNS ou les interfaces. Les adresses affichées sont celles publiées par `ip` pour chaque interface. Les interfaces absentes, les compteurs inaccessibles et les informations Wi-Fi non exposées sont signalés comme indisponibles plutôt que supposés.

**Limites connues :** la passerelle est actuellement lue dans la table de routage IPv4 du noyau ; les routes IPv6, les VPN détaillés, les statistiques par application et les tests de débit ne sont pas encore intégrés. Le débit initial reste « — » jusqu'au deuxième relevé. La validation matérielle doit être réalisée sur une session Bazzite avec Ethernet, Wi-Fi et VPN.
