# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier Crobard, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Preview publiée : `0.9.17~ynh1`, branche `preview`, paquet `a8f71633e5e227f7a1d459c615a3a34179e78050`.
- Catalogue Preview publié : `b2a67ee6ac66f6f1deca9e3681b6a3ea606b4a3b` ; flux publics et manifeste vérifiés.
- Stable conservée en `0.9.16~ynh1`, paquet `2528740162206f86c286b711024c6b11865a4e88`.
- Candidate locale : `0.10.0~ynh1`, consultation client protégée par code.

## Lot actif

- Consultation extérieure : publication volontaire, lien permanent protégé par code, vue lecture seule et mesures temporaires.

## Dernière étape validée

- Le client confirme la mise à jour 0.9.16 et le nom Crobard dans l’application ; l’ancien nom persiste dans YunoHost.
- Preview 0.9.17 publiée : synchronisation des deux libellés YunoHost et nouveau rendu des mesures avec croix fines, aperçu et sélection du trait ou du texte.
- Candidate 0.10.0 développée localement ; parcours auteur/client testé sur données fictives, mobile et PDF natif jusqu’à ×50.

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

- Faire valider la V1 de consultation client ; préparer sa publication Preview puis exécuter la recette YunoHost isolée (SSO privé / consultation publique, HTTPS, backup/restore).
