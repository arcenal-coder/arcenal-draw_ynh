# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier ARCenal DRAW, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Application : `0.9.13~ynh1`.
- Code fonctionnel : non publié.
- Documentation et historique : non publiés.

## Lot actif

- Revue finale, nettoyage et durcissement avant production.

## Dernière étape validée

- Fonction d’archive renommée « Instantanés d’export » conformément à son comportement réel.

## Tests exécutés

- VALIDÉ : 51 tests automatisés locaux réussis pour la version `0.9.13~ynh1`.
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

- Exécuter la recette complète sur une instance YunoHost isolée avant d’autoriser la publication de production.
