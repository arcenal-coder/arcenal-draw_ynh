# Livraison Crobard 0.9.17~ynh1 — Preview

Date : 20 octobre 2026.

- Dépôt source : https://github.com/arcenal-coder/arcenal-draw_ynh
- Branche de livraison : `preview`.
- SHA du paquet : à renseigner après commit.
- Publication demandée et autorisée par Damien dans cette conversation.

## Contenu

- Mise à jour des libellés d’installation et de permission principale YunoHost vers Crobard, sans changement des autorisations.
- Mesures avec petites croix, trait fin, distance au-dessus et aperçu avant le second clic.
- Sélection par le trait ou le texte, puis suppression par corbeille ou clavier.
- Format des projets et mesures existants conservé.

## Preuves

- 57 tests Python : RÉUSSIS.
- `node tests/measurement_behaviour.cjs` : RÉUSSI, création, aperçu, distance calibrée, zoom ×1/×10/×50 et sélection/suppression.
- Syntaxes JavaScript, Python et Bash : RÉUSSIES.
- `git diff --check` : RÉUSSI.
- Linter YunoHost : six scripts acceptés ; résultat global PARTIEL, absence du catalogue public YunoHost et avertissements préexistants.
- Installation, mise à niveau, accès SSO, sauvegarde/restauration et suppression sur instance isolée : NON_EXÉCUTÉS.
- Recette réelle du rendu, export PDF et libellé du portail par Damien : NON_EXÉCUTÉE.

## Diffusion et retour arrière

- Publication GitHub et résolution du Store Preview : en cours.
- Les catalogues sont épinglés sur un SHA complet ; aucune mise à jour de production n’est exécutée par cette livraison.
- Version précédente : `0.9.16~ynh1`, paquet `2528740162206f86c286b711024c6b11865a4e88`.
- Avant mise à niveau, conserver une sauvegarde YunoHost. Pour un retour complet, restaurer cette sauvegarde ; une correction fondée sur l’ancien code doit recevoir un numéro de version supérieur.
