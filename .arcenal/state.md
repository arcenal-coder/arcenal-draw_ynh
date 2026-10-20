# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier Crobard, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Preview publiée : `0.10.0~ynh1`, branche `preview`, paquet `21531d12a9124344561cb31c970b644659c90d7a`.
- Catalogue Preview publié : `ffab97a19c2c20ea1cd29e7f9bc2746a05c24e2a` ; flux publics et manifeste vérifiés.
- Stable conservée en `0.9.16~ynh1`, paquet `2528740162206f86c286b711024c6b11865a4e88`.
- Consultation client protégée par code intégrée à Crobard ; aucune seconde application créée.
- Candidate locale non publiée : `0.10.1~ynh1`, cartouches, balisages multiples, alignement des outils et bouton Voir tout.

## Lot actif

- Finitions visuelles demandées par Damien, décrites dans `.arcenal/CARTOUCHE_REFINEMENT.md` ; montrer le résultat avant toute publication.

## Dernière étape validée

- Le client confirme la mise à jour 0.9.16 et le nom Crobard dans l’application ; l’ancien nom persiste dans YunoHost.
- Preview 0.9.17 publiée : synchronisation des deux libellés YunoHost et nouveau rendu des mesures avec croix fines, aperçu et sélection du trait ou du texte.
- Preview 0.10.0 publiée sur demande de Damien ; parcours auteur/client testé sur données fictives, mobile et PDF natif jusqu’à ×50. Validation réelle YunoHost encore NON_EXÉCUTÉE.

## Tests exécutés

- VALIDÉ : 69 tests Python, dont les accès à la consultation, et scénario JavaScript des mesures pour la candidate `0.10.0~ynh1`.
- VALIDÉ : syntaxes Python, JavaScript et Bash, puis contrôle des différences Git.
- VALIDÉ : aucune référence textuelle ou aucun chemin portant le nom du composant supprimé ne subsiste dans les fichiers suivis.
- VALIDATION PARTIELLE : six scripts acceptés par le linter officiel YunoHost ; code global 1 pour absence du catalogue public et avertissements préexistants.
- VALIDÉ : 23 tests automatisés du catalogue ARCenal réussis avant publication.
- VALIDÉ : workflows GitHub de vérification et de publication du Store réussis.
- NON EXÉCUTÉ : cycle de vie réel sur une instance YunoHost/Incus isolée.

## Décisions structurantes

- Formats importés : PDF, PNG et JPEG uniquement.
- Les formats CAO natifs ne font pas partie du périmètre de l’application.
- Export PDF WYSIWYG restauré depuis la version `0.9.9`.
- Les défauts de caractères déjà présents dans le PDF source doivent être corrigés lors de l’export AutoCAD.

## Blocages

- La recette installation, mise à niveau, sauvegarde/restauration et suppression reste à exécuter sur une instance YunoHost isolée.
- Le dossier non suivi `ARCenal_Dev-Harness/` est conservé sans modification et ne fait pas partie de l’application.

## Prochaine action

- Faire valider les captures de la candidate locale 0.10.1 avant publication. La recette YunoHost isolée reste nécessaire avant partage de plans clients.
