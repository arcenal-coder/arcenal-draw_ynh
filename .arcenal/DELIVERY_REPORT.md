# Livraison Crobard 0.9.17~ynh1 — Preview

## Candidate locale suivante — 0.10.0~ynh1

Développée le 20 octobre 2026, non publiée. Lot : `.arcenal/CLIENT_CONSULTATION.md`.
Publication volontaire d’une consultation client par lien permanent et code,
lecture seule, zoom/déplacement et mesures temporaires. Accès public limité au
sous-chemin `/consultation/` ; aucune action de production ni donnée réelle modifiée.

Contrôles : 69 tests Python, scénario JavaScript des mesures, syntaxes Python/JS/Bash,
recette navigateur locale sur données fictives (ouverture protégée, publication,
rechargement, mesures, mobile et PDF natif jusqu’à ×50). Linter YunoHost : six scripts
acceptés, résultat global partiel pour les avertissements catalogue public préexistants.
Résolution Store 0.10.0, installation, mise à niveau, cookies HTTPS et permissions
SSO réelles, sauvegarde/restauration, recette client : NON_EXÉCUTÉES.

Preuves visuelles locales non versionnées : `output/consultation-client-desktop.jpg`
et `output/consultation-client-mobile.jpg`. La base est étendue par création de tables
additives ; les fichiers publiés sont sauvegardés avec `data_dir`.

## Livraison publiée précédente

Date : 20 octobre 2026.

- Dépôt source : https://github.com/arcenal-coder/arcenal-draw_ynh
- Branche de livraison : `preview`.
- SHA du paquet : `a8f71633e5e227f7a1d459c615a3a34179e78050`.
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

- Publication GitHub sur `preview` : RÉUSSIE, paquet `a8f71633e5e227f7a1d459c615a3a34179e78050`.
- Référencement catalogue : commit initial `9605fee00a3e900b45e73f2c87709397eecc4b40`, promotion Preview `b2a67ee6ac66f6f1deca9e3681b6a3ea606b4a3b`.
- Workflow officiel de promotion : RÉUSSI, https://github.com/arcenal-coder/arcenal-systeme-catalogue/actions/runs/39391986786
- Workflow de publication : RÉUSSI, https://github.com/arcenal-coder/arcenal-systeme-catalogue/actions/runs/39392021922
- Flux publics `preview/v1/release.json` et `preview/v3/apps.json` : VÉRIFIÉS, même SHA, branche `preview`, nom Crobard et version 0.9.17. Manifeste du paquet accessible sur GitHub et cohérent.
- 23 tests du catalogue RÉUSSIS après promotion. Stable vérifiée inchangée en 0.9.16.
- Les catalogues sont épinglés sur un SHA complet ; aucune mise à jour de production n’est exécutée par cette livraison.
- Version précédente : `0.9.16~ynh1`, paquet `2528740162206f86c286b711024c6b11865a4e88`.
- Avant mise à niveau, conserver une sauvegarde YunoHost. Pour un retour complet, restaurer cette sauvegarde ; une correction fondée sur l’ancien code doit recevoir un numéro de version supérieur.
