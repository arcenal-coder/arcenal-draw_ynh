# Rapport de validation — ARCenal DRAW 0.9.15~ynh1

Date : 15 octobre 2026

## Contrôles locaux

| Contrôle | Résultat | Preuve |
|---|---|---|
| Compilation Python | RÉUSSI | `python3 -m py_compile backend/*.py` |
| Syntaxe JavaScript | RÉUSSI | `node --check app.js` avec Node.js 24.19.0 |
| Syntaxe Bash | RÉUSSI | `bash -n scripts/*` |
| Tests automatisés | RÉUSSI | 54 tests réussis |
| Propreté du diff | RÉUSSI | `git diff --check` sans erreur |
| Recherche de secrets | RÉUSSI DANS LE PÉRIMÈTRE | aucun secret détecté dans le code applicatif et les configurations ; les occurrences `password` de PDF.js sont des noms internes de la bibliothèque |
| Références au composant CAO retiré | RÉUSSI | aucune occurrence textuelle ou aucun chemin suivi restant |
| Linter officiel YunoHost | RÉUSSI POUR LE PAQUET PRIVÉ | scripts de cycle de vie acceptés ; les erreurs restantes concernent uniquement l’absence du catalogue public YunoHost |

## Cycle de vie YunoHost

| Scénario | Résultat | Justification |
|---|---|---|
| Installation neuve | NON_EXÉCUTÉ | aucune instance YunoHost/Incus isolée disponible localement |
| Accès SSO et permissions | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Mise à niveau depuis 0.9.12 | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette et une sauvegarde préalable |
| Sauvegarde/restauration | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Suppression/réinstallation | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Recette navigateur multi-postes | NON_EXÉCUTÉ | Safari, Chrome, Firefox et lecteurs PDF clients restent à vérifier |

## Limites ouvertes

- L’interface d’export déclenche l’impression WYSIWYG du navigateur. L’instantané d’export associé conserve l’état réouvrable du projet, pas le fichier PDF enregistré par l’utilisateur.
- Aucun quota par utilisateur ni limite de fréquence n’est encore appliqué aux imports et conversions. Les limites unitaires sont de 100 Mo par plan, 12 Mo par JSON et 150 Mo par PDF d’archive.
- Les logos et signatures n’ont pas encore de plafond de taille dédié avant leur décodage local dans le navigateur.
- PDF.js 4.10.38 est embarqué. Les options d’évaluation et de scripts sont explicitement désactivées ; une mise à niveau majeure doit faire l’objet d’une recette de rendu dédiée.
