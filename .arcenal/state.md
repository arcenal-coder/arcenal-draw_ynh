# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier Crobard, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Application publiée : `0.9.16~ynh1`. Candidate Preview : `0.9.17~ynh1`.
- Code fonctionnel publié : `2528740162206f86c286b711024c6b11865a4e88`.
- Catalogues ARCenal `development`, `preview` et `stable` publiés : `5dcdb65ad0728bd1fb3085fcffa2724b34f05195`.

## Lot actif

- Corriger le libellé YunoHost conservé après mise à jour et rendre les mesures précises, lisibles et supprimables.

## Dernière étape validée

- Le client confirme la mise à jour 0.9.16 et le nom Crobard dans l’application ; l’ancien nom persiste dans YunoHost.
- Candidate 0.9.17 : synchronisation des deux libellés YunoHost et nouveau rendu des mesures avec croix fines, aperçu et sélection du trait ou du texte.

## Tests exécutés

- VALIDÉ : 57 tests Python et scénario JavaScript de création, aperçu, calibrage, zoom et suppression des mesures pour la candidate `0.9.17~ynh1`.
- VALIDÉ : syntaxes Python, JavaScript et Bash, puis contrôle des différences Git.
- VALIDÉ : aucune référence textuelle ou aucun chemin portant le nom du composant supprimé ne subsiste dans les fichiers suivis.
- VALIDÉ : scripts du paquet acceptés par le linter officiel YunoHost ; contrôles du catalogue public non applicables au catalogue privé ARCenal.
- VALIDÉ : 16 tests automatisés du catalogue ARCenal réussis avant publication.
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

- Publication Preview 0.9.17 autorisée par Damien ; diffuser sur GitHub et dans ARCenal Store, puis faire vérifier le nom du portail et les mesures.
