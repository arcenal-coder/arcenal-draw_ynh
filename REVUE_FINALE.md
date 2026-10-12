# Revue finale avant production — ARCenal DRAW

Date : 12 octobre 2026
Version examinée : `0.9.13~ynh1`

## Architecture et données

ARCenal DRAW utilise une interface statique sans framework, une API WSGI Python, SQLite, Gunicorn, Nginx, Poppler et PDF.js. Le SSO YunoHost fournit l’identité au backend. Les données traitées comprennent des plans techniques, les positions et paramètres radiologiques, les informations de société, les noms, fonctions et signatures du réalisateur et du validateur, ainsi que les exports.

## Passe 1 — Nettoyage et syntaxe

- suppression du calcul SHA-256 inutilisé pendant l’import ;
- suppression d’un filtrage de clé jamais produite ;
- suppression de la dernière commande et des références à l’ancien convertisseur CAO ;
- actualisation du README et des versions de cache frontend ;
- compilation Python, syntaxe JavaScript et syntaxe Bash validées.

## Passe 2 — Architecture, robustesse et sécurité

### Vulnérabilité corrigée — contrôle d’accès horizontal

- Composants : `backend/app.py`, `backend/db.py`.
- Scénario : un utilisateur authentifié connaissant l’identifiant aléatoire d’un import pouvait demander son aperçu ou son original sans contrôle de propriétaire.
- Gravité : élevée, car un plan technique d’un autre utilisateur pouvait être divulgué ; l’identifiant aléatoire réduisait seulement la probabilité d’exploitation.
- Correction : contrôle obligatoire de l’association propriétaire/import avant toute lecture.
- Vérification : test `alice` autorisé et `bob` refusé par une réponse 404, sur l’aperçu et l’original.

### Robustesse des entrées

- Les corps JSON doivent désormais être des objets et les nombres non finis sont refusés.
- Les états d’archive, identifiants de projet et calibrages sont validés avant stockage.
- Les booléens, valeurs infinies, négatives ou nulles ne peuvent plus devenir un facteur de calibrage.
- Un import dont la conversion ou l’enregistrement échoue supprime son répertoire temporaire.

### Durcissement

- Réponses JSON non mises en cache et protégées contre le reniflage de type MIME.
- CSP, interdiction d’objets, protection anti-cadrage, politique de référent et permissions navigateur ajoutées à Nginx avec la directive compatible YunoHost `more_set_headers`.
- Évaluation dynamique et scripts PDF.js explicitement désactivés.
- Accès initial YunoHost limité aux utilisateurs authentifiés au lieu des visiteurs publics.
- Service systemd renforcé : masque de permissions, périphériques privés, noyau et espaces de noms protégés, familles réseau limitées et absence d’élévation de privilèges.

### Dépendances

- Aucun paquet `pip` ou `npm` à installer ; les dépendances serveur sont gérées par Debian/YunoHost.
- PDF.js embarqué est en version 4.10.38. L’avis officiel [GHSA-wgrm-67xf-hhpq](https://github.com/mozilla/pdf.js/security/advisories/GHSA-wgrm-67xf-hhpq) affecte les versions jusqu’à 4.1.392 : cette copie est postérieure et la défense `isEvalSupported: false` est appliquée.
- L’avis [GHSA-hq66-cqwq-w95j](https://github.com/mozilla/pdf.js/security/advisories/GHSA-hq66-cqwq-w95j) vise les versions 5.6.83 et suivantes avant 6.2.108 ; la version embarquée n’entre pas dans cette plage et les scripts sont désactivés explicitement.

## Passe 3 — Validation et régressions

- 51 tests automatisés réussis, dont les nouveaux tests d’isolation, validation, nettoyage d’échec et en-têtes de sécurité.
- Syntaxes Python, JavaScript et Bash validées.
- Diff Git sans erreur de formatage.
- Linter officiel YunoHost exécuté. Les scripts sont acceptés ; les alertes bloquantes affichées concernent uniquement l’absence de cette application privée dans le catalogue public YunoHost.
- Revue indépendante réalisée sans modification par un second agent ; ses constats confirmés ont été intégrés ou consignés.

## Risques restant à traiter

### Décision fonctionnelle — instantanés d’export

Le navigateur imprime la feuille WYSIWYG mais ne renvoie pas ensuite à l’application le fichier PDF enregistré par l’utilisateur. La fonction auparavant présentée comme une archive PDF est donc renommée « Instantanés d’export ». Chaque instantané conserve et réouvre l’état du projet au moment de l’export, sans prétendre contenir le PDF imprimé.

### Risque d’abus — quotas

Un compte authentifié peut multiplier les imports et conversions jusqu’à saturer le stockage ou les workers. Les limites par requête sont en place, mais pas les quotas cumulés ni la limitation de fréquence. Définir d’abord le volume légitime par utilisateur, puis ajouter un quota testable et une limite de conversion adaptée à l’infrastructure.

### Améliorations de durcissement non bloquantes

- Les logos et signatures sont traités localement par le navigateur sans plafond dédié avant décodage. Un fichier exceptionnellement lourd peut saturer l’onglet de son propre utilisateur. Une limite métier doit être fixée avant d’ajouter un refus arbitraire.
- Les suppressions associent une transaction SQLite et une suppression de fichier sans transaction commune possible. Une panne disque au mauvais moment peut laisser un fichier orphelin ou une métadonnée sans fichier ; prévoir une tâche de réconciliation si le volume d’usage le justifie.
- PDF.js est livré en copie versionnée, sans gestionnaire de dépendances. Sa version et les avis officiels doivent être contrôlés à chaque préparation de release.

### Vérifications d’infrastructure

Le cycle réel installation, upgrade, sauvegarde/restauration, suppression et accès SSO doit être exécuté sur une instance YunoHost isolée avant production. Aucun test intrusif ni aucune modification du serveur réel n’a été réalisé.

Sur une installation existante, vérifier aussi dans l’administration YunoHost que la permission principale de l’application est limitée aux utilisateurs authentifiés : la nouvelle valeur par défaut du manifeste ne doit pas être considérée comme la preuve qu’une permission historique a été modifiée.

## Verdict

Validation partielle. Le code contrôlé est nettement durci et toutes les validations locales réussissent. La décision sur les instantanés d’export est intégrée. La mise en production reste bloquée jusqu’à la recette complète YunoHost. Le quota d’usage doit être traité avant une ouverture à un grand nombre d’utilisateurs non supervisés.
