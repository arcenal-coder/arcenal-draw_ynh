# ARCenal DRAW — Historique de conception et des versions

Dernière mise à jour : 9 octobre 2026  
Version courante au moment de la rédaction : `0.9.12~ynh1`  
Dépôt : <https://github.com/arcenal-coder/arcenal-draw_ynh>

## Objet du document

Ce document conserve les décisions de conception, les évolutions fonctionnelles et les corrections techniques d’ARCenal DRAW. Il sert à :

- comprendre pourquoi une fonction existe et comment elle a évolué ;
- identifier rapidement la version ayant introduit une régression ;
- retrouver un état antérieur précis dans Git ;
- éviter de réintroduire des solutions déjà abandonnées ;
- préparer les futures versions avec un historique lisible.

Les numéros `~ynhN` désignent les révisions du paquet YunoHost. Les identifiants placés après chaque version sont les commits Git de référence.

## Principes de conception permanents

- KISS et YAGNI : rester simple, éprouvé et fiable.
- Dépendances limitées au strict nécessaire.
- Formats d’entrée retenus : PDF, PNG et JPEG.
- Le PDF demeure le format de référence pour les plans techniques.
- Calibration en mètres à partir de deux points connus.
- WYSIWYG à l’export : le PDF doit reprendre exactement la feuille visible.
- Données de projet, plans réutilisables et archives conservés après fermeture.
- Interface utilisable à la souris, à la molette et sur différentes tailles d’écran.
- Toutes les zones d’une fusion appartiennent à la même société ou équipe.
- Le cartouche s’adapte au contenu visible et au niveau de zoom du plan.

## Phase de conception avant publication

Le prototype initial a défini les fonctions métier suivantes avant la création du paquet YunoHost :

- feuille A3 paysage ou portrait ;
- cartouche compact inspiré des plans INEXCO ;
- date, localisation, client, société, source, activité, horaires de tirs, échelle, réalisation et validation ;
- choix Iridium-192 ou Sélénium-75 et activité en Ci ou TBq ;
- calcul de distance pour 2,5 µSv/h ou 25 µSv sur une heure ;
- atténuation 1/250 activée par défaut et possibilité de la désactiver ;
- distance de balisage réglable manuellement ;
- ajout de plusieurs sociétés avec couleurs distinctes ;
- points d’impact portant un symbole radiologique ;
- fusion et dissociation des zones en respectant le contour exact des cercles ;
- surbalisage optionnel à distance, couleur, style et épaisseur réglables ;
- outils de signalement : panneau interdit, gyrophare, barrière et cône ;
- suppression par la corbeille ou les touches Retour/Supprimer ;
- déplacement du plan, zoom à la molette et calibration ultérieure ;
- mémorisation du travail après export et reprise des projets.

## Historique détaillé

### 0.1 — Premier paquet YunoHost

#### `0.1.0~ynh1` — 2 octobre 2026 — `e0cefb5`

- Création du premier paquet YunoHost public d’ARCenal DRAW.
- Mise en place de l’application web, du manifeste, des scripts d’installation, de mise à niveau, de sauvegarde et de restauration.
- Première intégration au catalogue ARCenal en canal de prévisualisation.

#### Maintenance `0.1.0`

- `12aa070` : suppression des caches produits par le linter YunoHost.
- `e278f66` : exclusion durable de ces caches dans Git.
- `a95a6e7` : contrôle du catalogue officiel rendu informatif afin de ne pas bloquer le paquet privé ARCenal.
- `0.1.0~ynh2` — `51a7c7d` : redirection correcte vers l’URL avec barre oblique finale lorsque l’application est installée dans un sous-chemin.
- `0.1.0~ynh3` — `cb38009` : adoption des helpers de sauvegarde YunoHost 2.1.
- `0.1.0~ynh4` — `31f4ccb` : correction des droits permettant à nginx de lire et servir les fichiers web.

### 0.2 — Import et affichage des plans

#### `0.2.0~ynh1` — 2 octobre 2026 — `7f3cad0`

- Premier affichage d’un plan importé dans l’éditeur.
- Liaison entre la zone de dépôt, le stockage serveur et la feuille de dessin.

#### `0.2.0~ynh2` — `15c1fc2`

- Ajout de l’avancement d’import.
- Affichage explicite des erreurs de chargement et de conversion.

### 0.3 — Moteur PDF natif et stabilisation YunoHost

#### `0.3.0~ynh1` — 2 octobre 2026 — `485b60d`

- Abandon du simple aperçu bitmap au profit d’un rendu PDF natif par tuiles.
- Amélioration de la qualité lors des forts zooms.
- Préparation d’un affichage plus fluide des grands plans.

#### Expérience de compatibilité `0.3.0`

- `0.3.0~ynh2` — `b949cd6` : compatibilité temporaire avec les anciens aperçus de plans.
- Retour à `0.3.0~ynh1` — `6395d18` : suppression de cette compatibilité, jugée inutile et trop complexe.

#### `0.3.1~ynh1` — `00806d1`

- Conservation correcte du chemin `/api` derrière le SSO et le proxy YunoHost.
- Correction des imports qui échouaient sans atteindre le backend.

#### `0.3.2~ynh1` — `9aba015`

- Déplacement des données persistantes vers `/var/lib/arcenal_draw`.
- Correction du plantage Gunicorn causé par l’écriture interdite dans `/home/yunohost.app`.

#### `0.3.3~ynh1` — 3 octobre 2026 — `34f768e`

- Déclaration correcte du type MIME JavaScript pour les modules PDF.js.
- Correction de l’erreur « application/octet-stream is not a valid JavaScript MIME type ».

#### `0.3.4~ynh1` — `de63376`

- Remplacement des extensions PDF.js problématiques par des extensions JavaScript standards.
- Compatibilité renforcée avec nginx et les navigateurs.

#### `0.3.5~ynh1` — `ba9c036`

- Masquage du fond de démonstration lorsqu’un vrai plan est chargé.
- Suppression de la superposition entre le plan test et le PDF importé.

#### `0.3.6~ynh1` — `eadfbf1`

- Suppression définitive du fond de plan de démonstration et du code associé.
- Nettoyage de l’interface et du modèle de données.

### 0.4 — Mesure et expérimentation DWG

#### `0.4.0~ynh1` — 3 octobre 2026 — `8945e6c`

- Ajout de l’outil de mesure entre deux points.
- Utilisation de la calibration du document pour afficher une distance en mètres.
- Persistance des mesures dans les projets.

#### `0.4.1~ynh1` — `ac063b2`

- Intégration expérimentale de LibreDWG au paquet YunoHost.
- Conversion DWG vers DXF avant exploitation.

#### Maintenance LibreDWG

- `0b94417` : compilation limitée au convertisseur réellement nécessaire afin d’alléger le paquet.
- `0.4.2~ynh1` — `9478d1c` : tolérance des avertissements DWG non bloquants relatifs aux classes instables.
- `0.4.3~ynh1` — 4 octobre 2026 — `c87c5c4` : conservation des définitions de blocs nécessaires lors de la lecture DXF.

### 0.5 — Abandon du moteur CAO embarqué

#### `0.5.0~ynh1` — 6 octobre 2026 — `601599e`

- Décision structurante : abandon de l’import DWG/DXF direct.
- Suppression des fonctions utilisateur liées à ces formats.
- Recentrage sur des plans PDF fiables, complétés ensuite par PNG et JPEG.
- Motif : rendu LibreDWG/DXF irrégulier, calques incomplets, blocs manquants et traits difficiles à normaliser automatiquement.

#### Nettoyage et compatibilité de mise à niveau

- `4776900` : retrait de la construction obsolète du moteur CAO dans l’intégration continue.
- `92e3190` : conservation des aperçus PDF existants pendant une mise à niveau depuis une ancienne version.

### 0.6 — Rendu optimisé des PDF et images

#### `0.6.0~ynh1` — 6 octobre 2026 — `d1f83db`

- Optimisation différenciée des plans PDF, PNG et JPEG.
- Conservation du PDF vectoriel lorsque le document le permet.
- Amélioration de la fluidité des déplacements et du zoom.

#### `0.6.1~ynh1` — `c7590fb`

- Repli automatique vers le PDF original lorsque l’aperçu SVG ne peut pas être affiché.
- Prévention des écrans vides après une conversion techniquement réussie.

#### `0.6.2~ynh1` — `6388b29`

- Ajout des recommandations d’export AutoCAD dans la zone d’import.
- Ajout d’une progression détaillée lors de l’analyse et de la conversion SVG.
- Recommandation de désactiver les épaisseurs d’objet dans le PDF source.

### 0.7 — Bibliothèques, archives et navigation

#### `0.7.0~ynh1` — 6 octobre 2026 — `b016350`

- Mémorisation des plans convertis dans « Plans déjà exploitables ».
- Conservation des projets en cours.
- Organisation des exports par date.
- Limitation des listes d’accueil aux éléments les plus récents.

#### `0.7.1~ynh1` — `5c1a0c4`

- Suppression possible des plans réutilisables et des exports archivés.

#### `0.7.2~ynh1` — `d8b0fd1`

- Ajout d’une option pour masquer ou afficher le cartouche dans le plan et le PDF.

#### `0.7.3~ynh1` — `184d2b0`

- Ajout des boutons `−` et `+` autour du réglage de zoom.
- Conservation du curseur de zoom existant.

#### `0.7.4~ynh1` — `e7c9c4c`

- Page d’accueil simplifiée.
- Affichage limité aux trois derniers exports avec recherche pour les plus anciens.
- Suppression de la recherche inutile dans la liste « Reprendre le travail ».

#### `0.7.5~ynh1` — `cf3a5b8`

- Repli sur le PDF original pour les conversions SVG trop volumineuses.
- Protection contre les aperçus trop lourds ou impossibles à injecter dans la page.

#### `0.7.6~ynh1` — `65de291`

- Correction des boutons de zoom.
- Correction du chargement indépendant de la bibliothèque de plans réutilisables.
- Réinitialisation correcte de la zone d’import après retour à l’accueil.

### 0.8 — Calibration, navigation et réactivité

#### `0.8.0~ynh1` — 6 octobre 2026 — `ff14d73`

- Simplification de la calibration : deux clics sur le plan puis saisie d’une seule distance connue en mètres.
- Suppression des paramètres techniques d’unité inutiles pour l’utilisateur.

#### `0.8.1~ynh1` — `856dfd4`

- Remplacement des gros points de calibration par des croix précises.
- Réduction de leur encombrement visuel.

#### `0.8.2~ynh1` — `938d566`

- Activation immédiate d’un curseur de visée lors du clic sur « Calibrer ».
- Croix de visée plus petite et légèrement renforcée.

#### `0.8.3~ynh1` — `f0c1ef4`

- Application correcte du coefficient de calibration à toutes les géométries métriques.
- Correction de la correspondance entre mesure, cercles et échelle graphique.

#### `0.8.4~ynh1` — `7d50e13`

- Zoom limité de 100 % à 1 000 %.
- Définition de 100 % comme affichage natif du document en pleine feuille.

#### `0.8.5~ynh1` — 7 octobre 2026 — `55c2b79`

- Navigation rendue plus fluide par aperçu rapide pendant le déplacement.
- Rendu précis différé à la fin du zoom ou du panoramique.
- Réduction de la latence ressentie.

#### `0.8.6~ynh1` — `16b0dd0`

- Extension du zoom jusqu’à 50× avec incréments de 0,5×.
- Premiers ajustements responsives des commandes, du cartouche et de la barre d’outils.
- Échap annule l’action et revient au mode Sélection.

#### `0.8.7~ynh1` — `b3f319d`

- Désactivation de la mise en cache durable du HTML après mise à niveau.
- Ajout d’un numéro de version aux ressources CSS et JavaScript.
- Correction des situations où YunoHost servait encore une ancienne interface.

#### `0.8.8~ynh1` — `5afa6e8`

- Taille visuelle du symbole de point d’impact stabilisée pendant le zoom.
- Suppression d’une équipe et de tous ses points d’impact depuis le cartouche modifiable, avec confirmation.

### 0.9 — Version métier consolidée

#### `0.9.0~ynh1` — 7 octobre 2026 — `323dee8`

- Nouveau parcours de calibration guidé par une fenêtre d’introduction.
- Conservation de la calibration lors de la création d’un nouveau projet à partir d’un plan déjà exploitable.
- Recalibration toujours disponible manuellement.

#### `0.9.1~ynh1` — `1d9445e`

- Zoom étendu à 50×.
- Première tentative d’export PDF vectoriel afin de préserver la finesse du plan.

#### `0.9.2~ynh1` — `cedd43f`

- Suppression des codes A, B, C affichés près des impacts et dans le cartouche.
- Déplacement des commandes de suppression dans le cartouche modifiable.
- Masquage des réglages de surbalisage lorsque l’option n’est pas activée.
- Finalisation du parcours d’export PDF.

#### `0.9.3~ynh1` — `5f51b80`

- Ajout de la sélection multiple rectangulaire des points d’impact.
- Sélection limitée automatiquement à une seule société.
- Utilisation plus simple dans les ensembles de cercles très denses.

#### `0.9.4~ynh1` — `f887188`

- Correction de la reprise des projets enregistrés.
- Nom des projets composé de la date, du client et de la localisation.
- Affichage des cinq projets les plus récents.
- Déplacement des informations du réalisateur vers la page d’accueil.

#### `0.9.5~ynh1` — `ec002c7`

- Persistance globale du nom, de la fonction et de la signature du réalisateur.
- Conservation de ces informations lors du retour à la page d’accueil.
- Attente de la fin de sauvegarde avant le rechargement des listes.
- Cette version est devenue la référence fonctionnelle pour l’export WYSIWYG.

#### `0.9.6~ynh1` — 8 octobre 2026 — `e619195`

- Expérience d’export PDF universel aplati à 600 DPI.
- Objectif : éviter les zones blanches observées dans certains lecteurs PDF et clients de messagerie.
- Limites constatées : fichier très lourd et traits de plan trop grossiers.

#### `0.9.7~ynh1` — `b865a33`

- Archivage du véritable fichier PDF exporté.
- Bouton « Afficher » ouvrant directement le PDF archivé.
- Conservation de cette fonction dans les versions suivantes.

#### `0.9.8~ynh1` — `f074611`

- Nouvelle tentative d’export vectoriel destinée à préserver la finesse des traits.
- Complexité et comportement jugés insuffisamment fiables selon les postes clients.

#### `0.9.9~ynh1` — `23c1c03`

- Retour volontaire à l’export WYSIWYG de la version 0.9.5.
- Suppression des moteurs d’export 600 DPI et de recomposition vectorielle.
- Conservation de l’archivage et du bouton « Afficher » introduits en 0.9.7.
- Version de référence à utiliser si une future évolution d’export régresse.

#### `0.9.10~ynh1` — `c3c609b`

- Fusion indépendante des surbalisages lorsque leurs cercles se touchent, même si les balisages standards restent séparés.
- Conservation des points d’impact et des zones standards d’origine.
- Dissociation possible du surbalisage fusionné.
- Nettoyage des fusions lors d’une suppression, d’une réattribution ou de la suppression d’une équipe.

#### `0.9.11~ynh1` — 9 octobre 2026 — `8f5cd51`

- Adoption de l’identité visuelle ONYX.
- Fond bleu clair avec dégradé léger vers le violet.
- Logo ONYX ajouté à la page d’accueil et au cartouche final.
- Paramètres réorganisés en sections Document, Validation, Client et logo.
- Première reprise approfondie des espacements et formulaires du panneau droit.

#### `0.9.12~ynh1` — `e53725f`

- Adaptation des formulaires à la largeur réelle du panneau par requêtes de conteneur CSS.
- Champ Activité rendu entièrement lisible, même sur écran étroit ou avec un fort zoom du navigateur.
- Passage automatique des cartes d’intervention sur une colonne lorsque nécessaire.
- Adaptation renforcée de l’en-tête, de la barre d’outils, du panneau droit, des paramètres et de la page d’accueil.
- Alignement vertical du logo ONYX et du titre « Plan de contrôle gammagraphique ».
- Nouvelle présentation d’accueil : « Outil de conception de plans d’impact radiologique ».

## Solutions abandonnées à ne pas réintroduire sans nouvelle validation

### Import DWG/DXF dans l’application

La chaîne LibreDWG puis DXF a été essayée entre les versions 0.4.1 et 0.4.3, puis supprimée en 0.5.0. Les problèmes observés concernaient les classes DWG instables, les définitions de blocs manquantes, les calques et la lisibilité des épaisseurs. La solution retenue est l’export PDF depuis AutoCAD avant import dans ARCenal DRAW.

### Aplatissement systématique en image 600 DPI

Essayé en 0.9.6. Il améliorait la compatibilité de certains lecteurs, mais produisait des fichiers lourds et dégradait la finesse des traits. Ne pas le réactiver comme export par défaut.

### Recomposition PDF vectorielle spécifique

Essayée en 0.9.8. Elle ajoutait une chaîne d’export délicate et pouvait diverger du rendu visible. Le choix actuel est l’impression WYSIWYG native restaurée en 0.9.9.

### Fond de démonstration permanent

Supprimé définitivement en 0.3.6 parce qu’il pouvait rester superposé au plan importé.

## Repères de débogage

| Symptôme | Première version à examiner | Zone probable |
|---|---:|---|
| Erreur 404 sous un sous-chemin YunoHost | 0.1.0~ynh2 | nginx, chemin d’installation |
| Erreur de sauvegarde YunoHost | 0.1.0~ynh3 | scripts `backup`/`restore` |
| nginx ne sert pas les fichiers | 0.1.0~ynh4 | permissions des fichiers web |
| Import sans réaction | 0.2.0~ynh2 ou 0.3.1 | interface d’import, proxy `/api` |
| Gunicorn redémarre en boucle | 0.3.2 | chemin des données, droits systemd |
| Erreur MIME PDF.js | 0.3.3–0.3.4 | nginx, fichiers PDF.js |
| Plan test superposé au PDF | 0.3.5–0.3.6 | ancien fond de démonstration |
| Mesure toujours égale à zéro | 0.4.0 ou 0.8.3 | calibration, conversion mètres/unités |
| PDF/SVG importé mais écran vide | 0.6.1 ou 0.7.5 | mécanisme de repli vers le PDF original |
| Plans réutilisables absents | 0.7.0 ou 0.7.6 | bibliothèque serveur, chargement accueil |
| Ancienne interface après mise à niveau | 0.8.7 | cache nginx et versions des ressources |
| Projet repris mais plan vierge | 0.9.4–0.9.5 | restauration du plan et sauvegarde différée |
| Export lourd ou traits grossiers | 0.9.6 | ancien export 600 DPI |
| Export différent de l’écran | 0.9.8–0.9.9 | recomposition vectorielle/WYSIWYG |
| Surbalisages non fusionnés | 0.9.10 | `overzoneMerges`, sélection multiple |
| Champ Activité coupé | 0.9.11–0.9.12 | grille responsive du panneau droit |

## Procédure de retour à une version

Avant toute opération, sauvegarder les données de l’application depuis YunoHost. Aucun tag Git historique n’existe actuellement ; les commits indiqués dans ce document sont donc les repères officiels.

Pour examiner une ancienne version sans modifier la branche principale :

```bash
git switch --detach <commit>
```

Pour créer une branche de diagnostic à partir d’une version :

```bash
git switch -c diagnostic/<description> <commit>
```

Pour annuler une modification précise sans réécrire l’historique :

```bash
git revert <commit>
```

Éviter `git reset --hard` sur le dépôt de travail. Pour YunoHost, une version de retour doit recevoir un numéro supérieur à la version installée, même si son code provient d’un ancien commit.

## Méthode recommandée pour les prochaines versions

À chaque publication :

1. augmenter la version dans `manifest.toml` ;
2. augmenter les paramètres de cache de `styles.css` et `app.js` dans `index.html` ;
3. ajouter la version au présent document avec la date et le commit ;
4. expliquer l’objectif utilisateur, les changements techniques et les risques de régression ;
5. lancer tous les tests locaux ;
6. publier l’application puis mettre à jour le catalogue ARCenal ;
7. vérifier les deux workflows GitHub ;
8. effectuer une sauvegarde YunoHost avant la mise à niveau de production.

## Format à reprendre pour une nouvelle entrée

```markdown
#### `X.Y.Z~ynh1` — date — `commit`

- Besoin utilisateur : …
- Modification fonctionnelle : …
- Modification technique : …
- Compatibilité/migration : …
- Risque ou zone à surveiller : …
- Tests réalisés : …
```
