# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier Crobard, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Application publiée : `0.9.16~ynh1`.
- Code fonctionnel publié : `2528740162206f86c286b711024c6b11865a4e88`.
- Catalogues ARCenal `development`, `preview` et `stable` publiés : `5dcdb65ad0728bd1fb3085fcffa2724b34f05195`.

## Lot actif

- Mise à jour YunoHost vers Crobard `0.9.16~ynh1` et recette finale du renommage.

## Dernière étape validée

- Crobard `0.9.16~ynh1` publié sur GitHub et diffusé dans les trois canaux du Store ARCenal.
- Workflows GitHub de vérification et de publication du catalogue terminés avec succès.

## Tests exécutés

- VALIDÉ : 55 tests automatisés locaux réussis pour la version `0.9.16~ynh1`.
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

- Mettre à jour l’application depuis l’administration YunoHost et vérifier l’affichage du nom Crobard.
