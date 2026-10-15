# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier ARCenal DRAW, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Application publiée : `0.9.15~ynh1`.
- Code fonctionnel publié : `55c64307ef08012accde85daf302ca6e0004efd5`.
- Catalogues ARCenal `development`, `preview` et `stable` publiés : `e35a291ffc7f58faa9628751a1bd380440fce373`.

## Lot actif

- Mise à jour YunoHost vers la version stable `0.9.15~ynh1` et recette visuelle finale.

## Dernière étape validée

- Version `0.9.15~ynh1` publiée sur GitHub et diffusée dans les trois canaux du Store ARCenal.
- Workflows GitHub de vérification et de publication du catalogue terminés avec succès.

## Tests exécutés

- VALIDÉ : 54 tests automatisés locaux réussis pour la version `0.9.15~ynh1`.
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

- Mettre à jour ARCenal DRAW depuis l’administration YunoHost, puis vérifier visuellement le cartouche et son export PDF.
