# Site officiel LEOS

Site statique, sans framework ni dépendance de build. Le contenu est servi depuis le dossier `website/`.

## Prévisualiser localement

Depuis la racine du dépôt :

```bash
python3 -m http.server 8080 --directory website
```

Puis ouvrir http://localhost:8080.

## Déployer avec GitHub Pages

1. Fusionner les changements du site dans la branche `main`.
2. Dans GitHub, ouvrir **Settings → Pages**.
3. Dans **Build and deployment → Source**, choisir **GitHub Actions**.
4. Vérifier que les permissions Pages / Actions du dépôt autorisent le déploiement.
5. Le workflow `.github/workflows/deploy-website.yml` publiera le contenu de `website/` à chaque modification de ce dossier sur `main`, ou via **Actions → Deploy LEOS website → Run workflow**.

Pour ce dépôt, l'URL GitHub Pages attendue est généralement `https://jovanille43.github.io/LEOS/`, sous réserve de l'activation effective de Pages et de l'état du déploiement. Aucun site n'est considéré comme publié tant que le workflow n'a pas réussi et que l'URL n'a pas été vérifiée.

## Préparer une publication ISO

Une ISO candidate standard a été générée et signée, mais sa validation physique n’a pas abouti. La section Téléchargements reste donc fermée. Ne pas y ajouter de lien tant que :
- l'ISO de la variante concernée a été construite ;
- les tests de démarrage et d'installation ont été réalisés ;
- le SHA-256 et le bundle de signature ont été générés et vérifiés ;
- les notes de version et les limites connues sont prêtes.

À la première publication, remplacer l'état « en préparation » par les liens réels vers la release officielle et ses fichiers de vérification. Ne jamais pointer vers un artefact éphémère de workflow.

## Personnalisation de marque

L'emblème affiché est une copie du fichier officiel `branding/gaming-logo.jpeg`. Le navigateur recolore dynamiquement ses zones chromatiques selon les Couleurs A et B sélectionnées, tout en conservant les détails métalliques et les variations de luminosité. Le dégradé de l'interface et ses accents utilisent ces mêmes deux couleurs.


## Thème du site

Le site reprend les réglages de la distribution LEOS :
- **Sombre / Clair / Auto** ; Auto passe en clair de 07:00 à 18:59 et en sombre de 19:00 à 06:59, selon l'heure locale du navigateur.
- **Couleur A et Couleur B** sont librement réglables ; le dégradé se met à jour en direct.
- Les valeurs initiales reprennent les valeurs par défaut de LEOS : `#00D9FF` et `#E33BFF`. Les couleurs choisies sur le site sont propres au navigateur et ne modifient pas les préférences d'une installation LEOS.

Les préférences du site sont conservées dans le stockage local du navigateur. Un site web hébergé ne peut pas lire directement le fichier de préférences privé d'une installation LEOS : la sélection sur le site est donc indépendante de celle du système, tout en reprenant les mêmes règles et valeurs de départ.
