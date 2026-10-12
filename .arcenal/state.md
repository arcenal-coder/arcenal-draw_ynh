# État du projet

Statut : ACTUEL

## Objectif

- Concevoir, maintenir et publier ARCenal DRAW, application YunoHost de création de plans d’impact radiologique à partir de fonds PDF, PNG ou JPEG.

## Version de référence

- Application : `0.9.12~ynh1`.
- Code fonctionnel : `e53725f`.
- Documentation et historique : `c8e0b9d`.

## Lot actif

- Maintenance corrective et amélioration continue ; aucun développement n’est actuellement autorisé ou engagé.

## Dernière étape validée

- Interface responsive renforcée, identité ONYX intégrée et historique complet des versions publié.

## Tests exécutés

- VALIDÉ : 44 tests automatisés réussis pour la version `0.9.12~ynh1`.
- VALIDÉ : workflow GitHub du paquet YunoHost réussi.
- VALIDÉ : catalogue ARCenal mis à jour vers `0.9.12~ynh1`.

## Décisions structurantes

- Formats importés : PDF, PNG et JPEG uniquement.
- DWG/DXF et LibreDWG abandonnés.
- Export PDF WYSIWYG restauré depuis la version `0.9.9`.
- Les défauts de caractères déjà présents dans le PDF source doivent être corrigés lors de l’export AutoCAD.

## Blocages

- Aucun connu.
- Le dossier non suivi `ARCenal_Dev-Harness/` est conservé sans modification et ne fait pas partie de l’application.

## Prochaine action

- Attendre le prochain besoin client, puis formaliser un seul lot court avant toute modification.
