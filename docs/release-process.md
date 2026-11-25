# Processus de publication versionnée LEOS

## Principe

La réussite d'une compilation ou la génération d'une ISO ne suffit pas à déclarer LEOS prêt à être diffusé. Aucune release stable ne doit être créée avant les validations en exécution sur une machine virtuelle puis sur du matériel physique de test.

La première publication publique envisagée est une préversion **`v0.1.0`**. Ce numéro est une proposition de jalon, pas une version publiée ni un tag existant.

## Critères obligatoires avant `v0.1.0`

- [ ] Le commit candidat est sur `main`, avec les contrôles Python et BlueBuild verts.
- [ ] L'ISO correspondant au même commit et aux images signées est généré avec succès.
- [ ] L'ISO démarre en UEFI dans QEMU/KVM et s'installe uniquement sur un disque virtuel dédié.
- [ ] KDE, le premier démarrage, les transitions Desktop/Gaming, l'audio et les vidéos sont testés dans la VM.
- [ ] Le système démarre et redémarre de façon fiable ; aucun service essentiel n'est en échec.
- [ ] Au moins une configuration physique est testée et consignée pour chaque variante annoncée comme prise en charge.
- [ ] Les limites connues (GPU, Wi-Fi, Bluetooth, veille, manettes, écrans) sont documentées ; aucune compatibilité universelle n'est revendiquée.
- [ ] Le checksum SHA-256, le digest source et les notes de version sont vérifiés.
- [ ] Les droits des ressources de marque et médias distribués sont documentés dans [ASSET-LICENSING.md](../ASSET-LICENSING.md).

Une variante matérielle qui n'a pas été testée physiquement ne doit pas être présentée comme certifiée. Elle peut rester expérimentale et être explicitement identifiée comme telle.

## Numérotation

Utiliser une version sémantique :
- `MAJOR` pour une incompatibilité majeure ou une évolution d'architecture ;
- `MINOR` pour une nouvelle fonctionnalité compatible ;
- `PATCH` pour une correction compatible.

Les premières versions de validation restent en `0.x.y`. Le tag et le titre de la release suivent le format `vX.Y.Z` (par exemple `v0.1.0` pour la première préversion qualifiée).

## Images candidates de pull request

Pour éviter de remplacer l'image stable `latest` pendant le développement, le workflow **Build LEOS** construit, pour une pull request issue du dépôt lui-même, uniquement la variante standard en image candidate signée. Les pull requests provenant d'un fork ne reçoivent pas de secrets de signature et ne déclenchent pas de publication d'image.

Après le succès du job **Build LEOS (AMD / Intel)**, une ISO candidate peut être produite manuellement depuis la branche de la pull request. Saisir le SHA complet (40 caractères) du commit source dans `source_commit`. Le workflow cherche alors dans le dépôt standard `leos` l'unique image signée dont le tag commence par les sept premiers caractères de ce SHA et un tiret. Il s'arrête si aucun tag ou plusieurs tags correspondent. BlueBuild publie un tag secondaire `<short_sha>-<os_version>` pour cette résolution. Aucun tag arbitraire comme `latest` n'est accepté.

La génération d'ISO ne propose que la variante standard. Le workflow vérifie la signature, fixe le digest, contrôle la structure de l'ISO et démarre l'installateur en UEFI/QEMU avant de publier l'artefact. Cette vérification automatique atteint l'interface Web Anaconda ; elle ne valide pas à elle seule une installation complète ni le premier démarrage de LEOS.

Cette ISO candidate n'est pas une release et ne remplace pas le jalon de validation complète en VM puis sur matériel réel.

## Procédure de publication

1. Geler un commit candidat sur `main` et vérifier que les contrôles automatiques sont verts.
2. Générer uniquement l’ISO standard à partir de l’image publiée et signée correspondant au commit candidat.
3. Vérifier chaque ISO avec son fichier SHA-256 et conserver le fichier `.source-digest`.
4. Préparer les notes depuis [CHANGELOG.md](../CHANGELOG.md), en séparant fonctions validées, limites connues et variantes expérimentales.
5. Créer un tag annoté `vX.Y.Z` sur le commit exact validé.
6. Créer une GitHub Release liée à ce tag et joindre, pour chaque variante publiée, l'ISO, le fichier `.sha256`, le fichier `.source-digest` et le manifeste `.manifest.json` généré après le contrôle UEFI/QEMU.
7. Mentionner les modèles/configurations réellement testés, les prérequis, les limites connues et le chemin de récupération.
8. Vérifier depuis la page de la release que tous les fichiers sont téléchargeables et que leurs sommes correspondent.

Ne pas publier l'ISO uniquement comme artefact de workflow pour une distribution durable : les artefacts Actions ont une durée de conservation limitée. La release versionnée devient le point de téléchargement stable.

## Contenu minimal des notes de version

- Version et commit source ;
- date de publication ;
- variantes matérielles incluses ;
- liens vers les ISO et checksums ;
- SHA-256 des ISO, digest(s) des images sources et manifestes de provenance incluant commit, variante et périmètre de validation ;
- matrice matérielle effectivement testée ;
- fonctions connues comme validées ;
- problèmes connus et procédures de récupération ;
- mention explicite de toute variante expérimentale.

## État au 20 novembre 2026

- La CI Python et BlueBuild de la branche `main` a validé l'intégration de l'import de jeux console sélectionnés (Dolphin, PCSX2, PPSSPP) et de la détection des manettes génériques Linux.
- Les améliorations Gaming (typographie lisible, propriétés d'accessibilité Qt, états vides guidés, aide clavier/manette et protection contre l'application concurrente du dock) ont été fusionnées après validation complète de leurs contrôles Python et BlueBuild/QML.
- L'ISO standard du run [#44729268412](https://github.com/jovanille43/LEOS/actions/runs/44729268412) a été installée avec succès dans une VM QEMU/KVM : compte Anaconda créé, installation terminée, redémarrage et bureau KDE atteints.
- Cette ISO a été construite depuis le commit `3c97827f5c658ed246a7b96ed4a5e8e1fbb2f317` ; elle ne contient donc pas encore les nouvelles fonctions fusionnées ensuite.
- Après une modification du code ou des recettes qui affecte l'image et fusionnée dans `main`, le workflow **Build LEOS** démarre automatiquement et publie les images signées. Après son succès, **Generate LEOS installer ISO** ne génère que l'ISO standard du même commit.
- Un lancement manuel exige le SHA complet du commit source ; le tag de l'image est résolu automatiquement et doit correspondre à ce SHA. Les variantes ISO NVIDIA et la sélection de tags arbitraires sont désactivées pour être reprises plus tard.
- Restent à vérifier dans la VM : sélecteur et transitions Desktop/Gaming, guide de premier démarrage, réseau, audio, services et redémarrages répétés. Les périphériques physiques et performances réelles restent à tester.
- Les ISO NVIDIA ne sont pas encore générées. Aucune release versionnée, aucun tag stable et aucune certification matérielle universelle ne sont publiés.


