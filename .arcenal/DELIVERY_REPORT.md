# Livraison Crobard 0.10.1~ynh1 — Preview

## Publication 0.10.1~ynh1

Autorisation de Damien le 20 octobre 2026, après présentation et validation des
captures locales. Même application YunoHost `arcenal_draw`, sans nouvelle installation.

- Lot : `.arcenal/CARTOUCHE_REFINEMENT.md`.
- Contenu : cartouches arrondis sans perte d’information, tous les balisages
  distincts visibles avec leurs distances, outils centrés et retour Voir tout.
- Source : https://github.com/arcenal-coder/arcenal-draw_ynh, branche `preview`.
- SHA du paquet : `fe7c9b269634f5d569bb3b2cc76e87919a7ac37b`.
- Tests locaux : 69 tests Python et deux scénarios JavaScript RÉUSSIS ; syntaxes
  JavaScript/Bash et `git diff --check` RÉUSSIS. Recherche ciblée de secrets sans résultat.
- Contrôles GitHub du paquet : RÉUSSIS, https://github.com/arcenal-coder/arcenal-draw_ynh/actions/runs/39427790253
- Référencement catalogue : `ff558ebe18403f734620ca61d6c1a39c513d3cc3`, 23 tests locaux RÉUSSIS.
- Contrôles catalogue : RÉUSSIS, https://github.com/arcenal-coder/arcenal-systeme-catalogue/actions/runs/39427931741
- Promotion Preview : RÉUSSIE, https://github.com/arcenal-coder/arcenal-systeme-catalogue/actions/runs/39428065713 ; catalogue `cbecc6d10733e81303395b7302f763bb7dc85f63`.
- Publication Store : RÉUSSIE, https://github.com/arcenal-coder/arcenal-systeme-catalogue/actions/runs/39428096045 ; flux publics v1/v3 cohérents avec le SHA du paquet et le manifeste `0.10.1~ynh1`. Stable inchangée en `0.9.16~ynh1`.
- Miroir GitHub Pages : VÉRIFIÉ sur les flux Preview v1/v3, même version et SHA. Le fichier partagé `assets/balisage.js` du paquet épinglé est accessible.
- Le workflow officiel actualise aussi les métadonnées de ses sources YunoHost (Dolibarr dans le flux v3) ; seule l’entrée `arcenal_draw` du manifeste de diffusion ARCenal a été promue. Aucun serveur client n’est mis à jour par cette génération.
- Aucune opération sur un serveur de production. Installation/mise à niveau,
  SSO/HTTPS et sauvegarde/restauration YunoHost de cette version : NON_EXÉCUTÉS.
- Retour arrière : sauvegarde YunoHost pré-mise à niveau à conserver et restaurer
  pour un retour complet. Paquet précédent : `21531d12a9124344561cb31c970b644659c90d7a`, version `0.10.0~ynh1`.

## Publication 0.10.0~ynh1

Développée et publication autorisée par Damien le 20 octobre 2026. Lot : `.arcenal/CLIENT_CONSULTATION.md`.
Publication volontaire d’une consultation client par lien permanent et code,
lecture seule, zoom/déplacement et mesures temporaires. Accès public limité au
sous-chemin `/consultation/` ; aucune action de production ni donnée réelle modifiée.

Contrôles : 69 tests Python, scénario JavaScript des mesures, syntaxes Python/JS/Bash,
recette navigateur locale sur données fictives (ouverture protégée, publication,
rechargement, mesures, mobile et PDF natif jusqu’à ×50). Linter YunoHost : six scripts
acceptés, résultat global partiel pour les avertissements catalogue public préexistants.
Installation, mise à niveau, cookies HTTPS et permissions SSO réelles,
sauvegarde/restauration, recette client : NON_EXÉCUTÉES. Cette publication ne vaut
pas validation de production ; vérifier le sous-chemin public et le maintien du
SSO privé sur une instance de recette avant partage de données clients.

- Source : https://github.com/arcenal-coder/arcenal-draw_ynh, branche `preview`.
- SHA du paquet : `21531d12a9124344561cb31c970b644659c90d7a`.
- Contrôles GitHub du paquet : RÉUSSIS, https://github.com/arcenal-coder/arcenal-draw_ynh/actions/runs/39400963352
- Référencement catalogue : `9cebd9a1a400353a08dab7fe74feaa322541c6f9`, seule application modifiée : `arcenal_draw`.
- Contrôles GitHub du catalogue : RÉUSSIS, https://github.com/arcenal-coder/arcenal-systeme-catalogue/actions/runs/39401045391
- Workflow officiel de promotion Preview : RÉUSSI, https://github.com/arcenal-coder/arcenal-systeme-catalogue/actions/runs/39401152407
- Catalogue Preview : `ffab97a19c2c20ea1cd29e7f9bc2746a05c24e2a`. Flux publics bruts `preview/v1/release.json` et `preview/v3/apps.json` VÉRIFIÉS : version `0.10.0~ynh1`, branche `preview` et SHA exact du paquet, manifeste GitHub cohérent. Stable inchangée en `0.9.16~ynh1`.
- Workflow de publication du Store : RÉUSSI, https://github.com/arcenal-coder/arcenal-systeme-catalogue/actions/runs/39401192353 ; miroir GitHub Pages vérifié sur les flux Preview v1 et v3, même version et SHA.
- 23 tests du catalogue RÉUSSIS après promotion. Aucune mise à jour de serveur exécutée.
- Retour arrière : conserver la sauvegarde YunoHost précédant la mise à niveau et la restaurer pour un retour complet. Paquet précédent : `a8f71633e5e227f7a1d459c615a3a34179e78050`, version `0.9.17~ynh1`.

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
