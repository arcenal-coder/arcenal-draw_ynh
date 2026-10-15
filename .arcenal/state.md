# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier ARCenal DRAW, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Application en préparation : `0.9.14~ynh1`.
- Code fonctionnel publié : `5bd19b5ecdf70f046c20fd8764f12ae59755229a`.
- Catalogues ARCenal `development` et `preview` publiés : `20b226ef1c5f559940e5a995a0371037d1f690f6`.

## Lot actif

- Correction du changement de balisage après dépôt et amélioration de la lisibilité du cartouche.

## Dernière étape validée

- Changement de seuil disponible pour une sélection simple ou fusionnée et police du cartouche augmentée de 20 %.

## Tests exécutés

- VALIDÉ : 53 tests automatisés locaux réussis pour la version `0.9.14~ynh1`.
- VALIDÉ : syntaxes Python, JavaScript et Bash, puis contrôle des différences Git.
- VALIDÉ : aucune référence textuelle ou aucun chemin portant le nom du composant supprimé ne subsiste dans les fichiers suivis.
- VALIDÉ : scripts du paquet acceptés par le linter officiel YunoHost ; contrôles du catalogue public non applicables au catalogue privé ARCenal.
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

- Vérifier visuellement le cartouche et le changement de balisage, puis préparer la publication de `0.9.14~ynh1` après confirmation humaine.
