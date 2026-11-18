# Signature et vérification Cosign de LEOS

## État actuel

La paire de clés de signature LEOS est configurée et les trois images conteneur ont été publiées et signées dans GHCR. Le fichier public `cosign.pub` est versionné à la racine du dépôt.

GitHub Actions utilise deux secrets de dépôt :
- `SIGNING_SECRET` : clé privée Cosign chiffrée ;
- `COSIGN_PASSWORD` : phrase de déverrouillage de cette clé.

Leur contenu est confidentiel. Ne jamais les afficher, les copier dans un ticket, les transmettre dans une conversation ou les committer. Les workflows ne doivent jamais écrire la clé privée dans le dépôt.

## Publication d'une nouvelle image

Le workflow manuel `.github/workflows/build.yml` :
1. exécute les contrôles Python, QML, ressources de marque et recettes BlueBuild ;
2. vérifie la présence des deux secrets et de `cosign.pub` ;
3. vérifie hors ligne que la clé privée fournie par le secret correspond à la clé publique ;
4. construit, publie et signe les variantes standard, NVIDIA legacy et NVIDIA open.

Les builds de publication sont manuels. Ne pas lancer le workflow pour une simple vérification documentaire ou pour retester une ISO déjà générée.

## Vérification d'une image publiée

Le workflow `.github/workflows/iso.yml` résout d'abord le tag GHCR vers un digest immuable, puis vérifie l'image avec la clé publique LEOS avant de générer l'ISO. La commande de vérification conserve le contrôle de la signature et des revendications de l'image :

```bash
cosign verify --insecure-ignore-tlog --check-claims --key cosign.pub <image-avec-digest>
```

Le paramètre `--insecure-ignore-tlog` évite une recherche Rekor pour les signatures LEOS actuellement publiées sans bundle de transparence. Il ne supprime pas la vérification cryptographique de la signature par la clé publique ni le contrôle des revendications de l'image. Ne pas remplacer cette vérification par une simple comparaison de tag ou de digest.

Le workflow vérifie aussi que le tag continue de désigner le digest vérifié avant et après la génération de l'ISO.

## Contrôle local ou rotation de clé

Ne régénérer une paire que dans le cadre d'une rotation planifiée ou après un incident. Utiliser une machine de confiance, un dossier privé et une phrase secrète forte ; laisser Cosign demander la phrase secrète de manière interactive. Ne jamais utiliser une phrase vide ni placer la phrase secrète dans la ligne de commande.

Avant toute rotation :
1. préparer une nouvelle clé publique et une sauvegarde chiffrée de la clé privée ;
2. planifier le remplacement coordonné des secrets GitHub et de `cosign.pub` ;
3. vérifier la nouvelle paire avec le script `tools/verify-cosign-key-pair.sh` ;
4. publier une nouvelle image signée et vérifier son digest ;
5. documenter la date et le motif de la rotation sans enregistrer de secret.

Si une clé privée est soupçonnée d'avoir été exposée, considérer les images signées par cette clé comme potentiellement compromises et interrompre les nouvelles publications jusqu'à la rotation.

## Vérifications et confidentialité

- Le script `tools/verify-cosign-key-pair.sh` effectue un test temporaire hors ligne.
- Le workflow Python utilise une paire de test jetable ; il ne lit pas les secrets de production.
- Le workflow de build valide les secrets sans en afficher les valeurs.
- Les logs GitHub Actions et les artefacts ne doivent contenir aucune clé privée ni phrase secrète.

Voir aussi [la procédure de construction](build.md) et [le processus de publication LEOS](release-process.md).
