# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier ARCenal DRAW, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Application publiée : `0.9.14~ynh1`.
- Code fonctionnel publié : `b63398c3761d094f5ca97762fcf9be681b41b54b`.
- Catalogues ARCenal `development`, `preview` et `stable` publiés : `1d00f6e1caeb3e6988b5d1a1d1741edfcd52943c`.

## Lot actif

- Mise à jour YunoHost vers la version stable `0.9.14~ynh1` et recette finale.

## Dernière étape validée

- Version `0.9.14~ynh1` publiée sur GitHub et diffusée dans les trois canaux du Store ARCenal.
- Workflows de vérification et de publication du catalogue terminés avec succès.

## Tests exécutés

- VALIDÉ : 53 tests automatisés locaux réussis pour la version `0.9.14~ynh1`.
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

- Mettre à jour ARCenal DRAW depuis l'administration YunoHost, puis vérifier le changement de balisage et la lisibilité du cartouche.
