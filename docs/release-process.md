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

## Procédure de publication

1. Geler un commit candidat sur `main` et vérifier que les contrôles automatiques sont verts.
2. Générer les ISO des seules variantes qualifiées à partir des images publiées et signées.
3. Vérifier chaque ISO avec son fichier SHA-256 et conserver le fichier `.source-digest`.
4. Préparer les notes depuis [CHANGELOG.md](../CHANGELOG.md), en séparant fonctions validées, limites connues et variantes expérimentales.
5. Créer un tag annoté `vX.Y.Z` sur le commit exact validé.
6. Créer une GitHub Release liée à ce tag et joindre, pour chaque variante publiée, l'ISO, le fichier `.sha256` et le fichier `.source-digest`.
7. Mentionner les modèles/configurations réellement testés, les prérequis, les limites connues et le chemin de récupération.
8. Vérifier depuis la page de la release que tous les fichiers sont téléchargeables et que leurs sommes correspondent.

Ne pas publier l'ISO uniquement comme artefact de workflow pour une distribution durable : les artefacts Actions ont une durée de conservation limitée. La release versionnée devient le point de téléchargement stable.

## Contenu minimal des notes de version

- Version et commit source ;
- date de publication ;
- variantes matérielles incluses ;
- liens vers les ISO et checksums ;
- SHA-256 des ISO et digest(s) des images sources ;
- matrice matérielle effectivement testée ;
- fonctions connues comme validées ;
- problèmes connus et procédures de récupération ;
- mention explicite de toute variante expérimentale.

## État au 18 novembre 2026

Les trois images conteneur standard, NVIDIA legacy et NVIDIA open ont été construites, publiées et signées. L'ISO standard a été générée avec succès et reste à tester en VM puis sur matériel physique. Les ISO NVIDIA ne sont pas encore générées. Aucun tag de release ni aucune GitHub Release LEOS n'a été publié.
