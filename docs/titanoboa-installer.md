# Chaîne d’installation Live LEOS avec Titanoboa

## État

Cette chaîne est une **candidate de migration** développée sur la branche \`feature/titanoboa-installer\`. Elle n’a pas encore produit une ISO validée et ne doit pas être utilisée sur le PC principal. L’ancien workflow \`.github/workflows/iso.yml\` est laissé intact pour conserver une comparaison et un retour arrière.

Titanoboa est un outil expérimental destiné aux images bootc. Le workflow reprend l’architecture utilisée par Bazzite : une image Live KDE est construite à partir de Bazzite, l’image LEOS à installer est embarquée dans le stockage Podman du Live, puis Titanoboa transforme cette image Live en ISO. Références : [Titanoboa](https://github.com/ublue-os/titanoboa), [workflow ISO Bazzite](https://github.com/ublue-os/bazzite/blob/main/.github/workflows/build_iso.yml), [scripts d’installation Bazzite](https://github.com/ublue-os/bazzite/tree/main/installer).

## Flux de construction

1. Le workflow sélectionne explicitement une variante et un tag LEOS publiés.
2. Il récupère le digest immuable de l’image et vérifie sa signature Cosign avec \`cosign.pub\`.
3. Il construit une image Live KDE basée sur \`ghcr.io/ublue-os/bazzite:stable\`.
4. Le constructeur Live tire l’image LEOS cible, l’intègre dans le stockage Podman, puis contrôle que son digest correspond à celui vérifié par le workflow.
5. Titanoboa génère l’ISO depuis l’image Live. Le workflow contrôle ensuite son checksum, son catalogue UEFI et signe l’ISO ainsi que son manifeste.

Le secret \`SIGNING_SECRET\` reste uniquement dans GitHub Actions. La clé privée n'est ni copiée dans l'image Live, ni enregistrée dans le dépôt, ni incluse dans l'ISO.

## Déploiement Anaconda

Anaconda déploie d'abord l'image LEOS embarquée via \`ostreecontainer\` et le transport \`containers-storage\`, ce qui évite de retélécharger l'ensemble de l'image pendant l'étape initiale de déploiement. Un \`bootc switch\` final utilise ensuite la référence GHCR avec vérification obligatoire de la politique de signatures.

Les trois variantes LEOS déclarent une politique de conteneur dont la règle par défaut rejette les images non approuvées. Les trois dépôts LEOS GHCR ne sont acceptés qu'avec une signature Sigstore correspondant à la clé publique LEOS et à l'identité du dépôt.

Le profil Anaconda crée une entrée EFI distincte sous \`EFI/leos\`. Les hooks LEOS ne suppriment pas le dossier \`EFI/fedora\`, ne renomment pas de partition \`/boot\`, ne formatent pas de partition et ne lancent pas de commande destructive de disque. Le partitionnement proposé par Anaconda reste à examiner manuellement : cela ne constitue **pas** une garantie de dual boot.

## Journaux en cas d'échec

Le hook \`%onerror\` collecte, lorsqu'ils existent, les journaux Anaconda suivants : \`anaconda.log\`, \`packaging.log\`, \`program.log\`, \`storage.log\` et \`syslog\`. Il prépare une archive \`LEOS-installation-diagnostics.tar.gz\` sur le bureau du compte Live et tente d'afficher un extrait avec YAD. Les journaux peuvent contenir des informations personnelles ; il faut les examiner et les expurger avant de les partager.

## Validation obligatoire avant utilisation sur du matériel

- La validation BlueBuild doit confirmer les trois recettes et les fichiers de politique de signature.
- Les scripts shell doivent passer \`bash -n\` et les tests de contrat Python.
- Le workflow Titanoboa doit réellement construire l'image Live et l'ISO.
- \`xorriso\` doit confirmer le catalogue UEFI ; le checksum et les signatures doivent être valides.
- L'ISO doit démarrer dans une VM x86_64 UEFI.
- Anaconda doit s'ouvrir et installer l'image sur un disque virtuel vierge.
- Le système installé doit redémarrer et passer les contrôles \`bootc status\`, réseau, KDE et services.
- Un test dual boot distinct doit préserver un système UEFI existant dans une VM jetable.

Un build ou des tests statiques verts ne prouvent pas une installation réussie. Aucune nouvelle tentative sur le ThinkPad ne doit avoir lieu tant que le démarrage et l'installation dans la VM ne sont pas validés et que le checksum de l'ISO ainsi que de la clé USB n'est pas contrôlé.
