# Rapport de validation — Crobard 0.9.17~ynh1 (candidate Preview)

Date : 20 octobre 2026

## Contrôles locaux

| Contrôle | Résultat | Preuve |
|---|---|---|
| Compilation Python | RÉUSSI | `python3 -m py_compile backend/*.py` |
| Syntaxe JavaScript | RÉUSSI | `node --check app.js` avec Node.js 24.19.0 |
| Syntaxe Bash | RÉUSSI | `bash -n scripts/*` |
| Tests Python | RÉUSSI | 57 tests réussis, dont les commandes de libellé YunoHost et la propagation des erreurs |
| Mesures JavaScript | RÉUSSI | `node tests/measurement_behaviour.cjs` : création, aperçu non sauvegardé, distance calibrée, repères au zoom ×1/×10/×50, sélection et suppression |
| Propreté du diff | RÉUSSI | `git diff --check` sans erreur |
| Recherche de secrets | RÉUSSI DANS LE PÉRIMÈTRE | aucun secret détecté dans le code applicatif et les configurations ; les occurrences `password` de PDF.js sont des noms internes de la bibliothèque |
| Références au composant CAO retiré | RÉUSSI | aucune occurrence textuelle ou aucun chemin suivi restant |
| Linter officiel YunoHost | VALIDATION PARTIELLE | six scripts acceptés sur une copie sans espace dans le chemin ; code de sortie 1 pour absence du catalogue public YunoHost, avertissements préexistants de licence propriétaire, README, service et change_url |

## Cycle de vie YunoHost

| Scénario | Résultat | Justification |
|---|---|---|
| Installation neuve | NON_EXÉCUTÉ | aucune instance YunoHost/Incus isolée disponible localement |
| Accès SSO et permissions | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Mise à niveau depuis 0.9.16 et libellé du portail | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette et une sauvegarde préalable |
| Sauvegarde/restauration | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Suppression/réinstallation | NON_EXÉCUTÉ | nécessite une instance YunoHost de recette |
| Recette navigateur multi-postes | NON_EXÉCUTÉ | Safari, Chrome, Firefox et lecteurs PDF clients restent à vérifier |

## Limites ouvertes

- L’interface d’export déclenche l’impression WYSIWYG du navigateur. L’instantané d’export associé conserve l’état réouvrable du projet, pas le fichier PDF enregistré par l’utilisateur.
- Aucun quota par utilisateur ni limite de fréquence n’est encore appliqué aux imports et conversions. Les limites unitaires sont de 100 Mo par plan, 12 Mo par JSON et 150 Mo par PDF d’archive.
- Les logos et signatures n’ont pas encore de plafond de taille dédié avant leur décodage local dans le navigateur.
- PDF.js 4.10.38 est embarqué. Les options d’évaluation et de scripts sont explicitement désactivées ; une mise à niveau majeure doit faire l’objet d’une recette de rendu dédiée.
