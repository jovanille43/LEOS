# Configurer la signature Cosign de LEOS

LEOS signe ses images conteneur publiées dans GitHub Container Registry. Le workflow de génération ISO vérifie cette signature avant de produire un installateur. La clé privée ne doit jamais être ajoutée au dépôt, à une issue, à une pull request ou à une conversation.

## 1. Générer une paire de clés sur une machine de confiance

Installer Cosign depuis la documentation officielle Sigstore, puis travailler dans un dossier privé :

```bash
mkdir -m 700 leos-signing-key
cd leos-signing-key
umask 077
COSIGN_PASSWORD='' cosign generate-key-pair
```

Cosign crée deux fichiers :
- `cosign.key` : clé privée, **à garder secrète** ;
- `cosign.pub` : clé publique, destinée au dépôt.

Ne jamais téléverser `cosign.key` dans Git. Ne pas la copier dans le dossier du dépôt.

## 2. Enregistrer la clé privée dans GitHub

Depuis la racine du dépôt local, avec GitHub CLI authentifié et autorisé à gérer les secrets :

```bash
gh secret set SIGNING_SECRET --repo jovanille43/LEOS < /chemin/vers/leos-signing-key/cosign.key
```

La valeur enregistrée doit être le contenu PEM complet de `cosign.key`. Le secret ne doit pas être affiché dans le terminal, copié dans un ticket ou partagé.

## 3. Ajouter uniquement la clé publique au dépôt

Copier `cosign.pub` à la racine du dépôt, puis créer une pull request contenant ce seul fichier (et éventuellement cette documentation). Vérifier avant commit qu'aucune clé privée n'est suivie :

```bash
git status --short
git check-ignore cosign.key
git ls-files | grep -E '(^|/)cosign\.key$' && echo "ERREUR : clé privée suivie"
```

La clé publique doit correspondre à la clé privée stockée dans le secret. Le workflow `Build LEOS` effectue un test cryptographique de correspondance avant de lancer BlueBuild.

## 4. Vérifier le prérequis sans publier d'image

Après ajout de `cosign.pub` et du secret `SIGNING_SECRET`, lancer le workflow **Build LEOS** manuellement depuis GitHub Actions. Il exécute d'abord les tests, vérifie les ressources, contrôle la paire de clés puis construit et publie les trois variantes si tous les contrôles passent.

Ne lancer cette publication que lorsque la clé publique est présente et que le secret a été configuré. Le secret GitHub n'est pas lisible par les workflows de pull requests provenant de forks.

## 5. Sécurité et rotation

- Limiter les personnes autorisées à modifier les secrets du dépôt.
- Ne jamais journaliser `SIGNING_SECRET` ni le contenu de `cosign.key`.
- Si la clé privée est exposée, considérer toutes les images signées avec elle comme potentiellement compromises : générer une nouvelle paire, remplacer le secret, mettre à jour `cosign.pub` et documenter la rotation.
- Conserver une sauvegarde chiffrée et contrôlée de la clé privée selon la politique de sécurité du projet.

## État actuel

Le workflow exige déjà `SIGNING_SECRET` et `cosign.pub`. Tant que l'utilisateur responsable du dépôt n'a pas créé et configuré ces deux éléments, la publication signée et la génération ISO doivent rester bloquées. Les tests CI ordinaires ne remplacent pas cette configuration.
