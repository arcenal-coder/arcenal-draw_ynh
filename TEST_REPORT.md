# Rapport de validation — Crobard 0.10.0~ynh1 (candidate locale Preview)

Date : 20 octobre 2026

## Contrôles locaux

| Contrôle | Résultat | Preuve |
|---|---|---|
| Compilation Python | RÉUSSI | `python3 -m py_compile backend/*.py` |
| Syntaxe JavaScript | RÉUSSI | `node --check app.js` avec Node.js 24.19.0 |
| Syntaxe Bash | RÉUSSI | `bash -n scripts/*` |
| Tests Python | RÉUSSI | 69 tests, dont publication, isolation propriétaire, sessions/cookies, refus d’écriture publique, code erroné et limitation des essais, changement de code, expiration/révocation, refus SVG actif et persistance du fond publié |
| Mesures JavaScript | RÉUSSI | `node tests/measurement_behaviour.cjs` : création, aperçu non sauvegardé, distance calibrée, repères au zoom ×1/×10/×50, sélection et suppression |
| Propreté du diff | RÉUSSI | `git diff --check` sans erreur |
| Recherche de secrets | RÉUSSI DANS LE PÉRIMÈTRE | aucun secret détecté dans le code applicatif et les configurations ; les occurrences `password` de PDF.js sont des noms internes de la bibliothèque |
| Références au composant CAO retiré | RÉUSSI | aucune occurrence textuelle ou aucun chemin suivi restant |
| Linter officiel YunoHost | VALIDATION PARTIELLE | paquet 0.10.0 contrôlé sur une copie sans espace ; six scripts acceptés, code de sortie 1 pour absence du catalogue public YunoHost, avertissements préexistants de licence propriétaire, README, service et change_url |
| Recette navigateur locale | RÉUSSI DANS LE PÉRIMÈTRE | données fictives : publication de l’éditeur, ouverture par code, zoom/mesure temporaire, même lien après republication, nouvelle version au rechargement et mesures effacées, cartouche mobile 390×844, fond PDF natif jusqu’à ×50 sans erreur console |
| Syntaxe Nginx sur instance réelle | NON_EXÉCUTÉ | Nginx et YunoHost absents de ce poste ; le serveur local de recette ne remplace pas le SSO |

## Cycle de vie YunoHost

| Scénario | Résultat | Justification |
|---|---|---|
| Installation neuve | NON_EXÉCUTÉ | aucune instance YunoHost/Incus isolée disponible localement |
| Accès SSO et permissions | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Mise à niveau depuis 0.9.17 et accès public consultation | NON_EXÉCUTÉ | vérifier permission visiteurs limitée au sous-chemin, maintien de l’authentification principale et cookies HTTPS sur une instance isolée |
| Sauvegarde/restauration | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Suppression/réinstallation | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Recette navigateur multi-postes | NON_EXÉCUTÉ | Safari, Chrome, Firefox et lecteurs PDF clients restent à vérifier |

## Limites ouvertes

- Les publications de consultation et leurs métadonnées sont conservées ; aucune purge automatique de l’historique n’est incluse dans cette V1. Les fonds immuables utilisent des liens physiques lorsqu’ils partagent le même système de fichiers pour limiter le stockage.
- La session de consultation dure au maximum huit heures. Révocation/expiration sont vérifiées sur chaque lecture ; une page déjà ouverte contrôle son accès toutes les 60 secondes. Les copies ou captures déjà conservées par un destinataire ne peuvent pas être rappelées.
- La limitation applicative concerne la saisie des codes. La protection contre les attaques volumétriques relève aussi du frontal et de l’hébergement.
- La recette locale a utilisé Python 3.12 avec scrypt ; le Python 3.9 Apple échoue car il ne fournit pas `hashlib.scrypt`. Aucun mécanisme de hachage dégradé n’a été ajouté.

- L’interface d’export déclenche l’impression WYSIWYG du navigateur. L’instantané d’export associé conserve l’état réouvrable du projet, pas le fichier PDF enregistré par l’utilisateur.
- Aucun quota par utilisateur ni limite de fréquence n’est encore appliqué aux imports et conversions. Les limites unitaires sont de 100 Mo par plan, 12 Mo par JSON et 150 Mo par PDF d’archive.
- Les logos et signatures n’ont pas encore de plafond de taille dédié avant leur décodage local dans le navigateur.
- PDF.js 4.10.38 est embarqué. Les options d’évaluation et de scripts sont explicitement désactivées ; une mise à niveau majeure doit faire l’objet d’une recette de rendu dédiée.
