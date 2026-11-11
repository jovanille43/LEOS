# Bluetooth dans LEOS

## Objectif

Le Bluetooth est une fonctionnalité prise en charge officiellement dans les deux modes LEOS. Il doit permettre de connecter notamment des manettes, casques, écouteurs, enceintes, claviers et souris, dans la limite des capacités du matériel et des pilotes Linux.

## Architecture retenue

LEOS s'appuie sur la pile Bluetooth native de Bazzite/Fedora et KDE, sans créer de daemon parallèle ni remplacer les outils système :

- **BlueZ** fournit la pile Bluetooth Linux et le service système `bluetooth.service`.
- **KDE Plasma / Bluedevil** fournit l'interface native de recherche, d'association, de connexion et de suppression des périphériques.
- **PipeWire** gère le transport audio Bluetooth avec la pile audio du bureau.
- **LEOS Control Center** donnera un accès rapide aux réglages Bluetooth essentiels et renverra vers les paramètres KDE complets pour l'association et le dépannage.
- **Gaming Mode** utilisera les périphériques d'entrée déjà exposés par Linux. Il pourra afficher l'état de connexion et le niveau de batterie uniquement lorsque ces informations sont réellement disponibles.

## Comportement attendu

- Le Bluetooth doit être disponible dans Desktop Mode et Gaming Mode.
- L'utilisateur peut activer/désactiver le Bluetooth, rechercher, associer, connecter et oublier un périphérique depuis les paramètres natifs KDE.
- Les périphériques associés doivent pouvoir se reconnecter automatiquement lorsque le matériel, le firmware et le système le permettent.
- Les manettes Bluetooth compatibles apparaissent dans le Centre des manettes comme les manettes USB, sans remappage global caché.
- Aucun périphérique n'est associé, supprimé ou déconnecté automatiquement par LEOS sans action de l'utilisateur.
- LEOS ne doit pas désactiver le Bluetooth au lancement du Gaming Mode ni au changement de mode.

## Décision de packaging

Ne pas ajouter aveuglément un deuxième gestionnaire Bluetooth ou des services concurrents. La recette actuelle est basée sur Bazzite KDE : avant de modifier les paquets ou l'activation systemd, vérifier dans l'image construite la présence de BlueZ, de `bluetooth.service`, de Bluedevil et des modules audio nécessaires. Si un élément manque réellement, ajouter uniquement la dépendance manquante via le mécanisme BlueBuild adapté.

La présence de BlueZ dans Fedora est documentée par [Fedora Packages](https://packages.fedoraproject.org/pkgs/bluez/bluez/). Le composant Bluetooth de KDE repose sur BlueZ via Bluedevil/BluezQt ; l'audio Bluetooth est traité par PipeWire. La base exacte de Bazzite et sa configuration devront être vérifiées sur l'image LEOS elle-même.

## Tests obligatoires avant validation

1. Vérifier que `bluetooth.service` existe et démarre au démarrage.
2. Vérifier qu'un adaptateur Bluetooth interne et un adaptateur USB sont détectés lorsqu'ils sont présents.
3. Associer, déconnecter, reconnecter et oublier un casque audio.
4. Vérifier les profils audio disponibles (lecture et microphone lorsque pris en charge).
5. Associer et reconnecter une manette Xbox, PlayStation et Nintendo compatible.
6. Vérifier clavier et souris Bluetooth.
7. Vérifier la persistance des associations après redémarrage.
8. Vérifier que les périphériques restent connectés lors du passage Desktop Mode ↔ Gaming Mode.
9. Vérifier que l'interface Gaming n'affiche pas un état ou une batterie non fournis par le système.

Ces tests doivent être réalisés sur du matériel réel. Une recette BlueBuild valide ou des tests Python réussis ne suffisent pas à certifier la compatibilité Bluetooth.
