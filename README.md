# Crobard

Crobard est une application YunoHost de conception de plans d’impact radiologique. Elle importe des fonds PDF, PNG ou JPEG, permet leur calibrage métrique, ajoute les zones de balisage, conserve des instantanés d’export réouvrables et produit un export PDF WYSIWYG par la fonction d’impression du navigateur.

## Architecture

- interface statique HTML, CSS et JavaScript sans framework ;
- API WSGI Python servie par Gunicorn derrière Nginx ;
- authentification transmise par le SSO YunoHost ;
- SQLite pour les projets, instantanés d’export et métadonnées ;
- Poppler pour convertir la première page des PDF vectoriels en SVG ;
- PDF.js embarqué pour l’affichage progressif des PDF restant natifs.
- consultation client dédiée sous `/consultation/`, publication volontaire et accès par code, sans compte YunoHost.

Les données persistantes sont placées dans `/var/lib/arcenal_draw` par la ressource `data_dir` YunoHost. Les formats CAO natifs ne font pas partie du périmètre.

## Vérifications locales

Depuis la racine du dépôt :

```sh
PYTHONPYCACHEPREFIX=/tmp/arcenal-draw-pycache python3 -m py_compile backend/*.py
node --check app.js
node --check sharing.js
node --check public/viewer.js
node tests/measurement_behaviour.cjs
bash -n scripts/*
PYTHONPYCACHEPREFIX=/tmp/arcenal-draw-pycache python3 -m unittest discover -s tests -v
git diff --check
```

Il n’existe ni dépendance Python installée par `pip`, ni compilation frontend, ni étape de build. Le paquet s’appuie uniquement sur les paquets APT déclarés dans `manifest.toml` et sur les fichiers statiques versionnés.

Les tests de consultation nécessitent un Python avec `hashlib.scrypt` (Python Debian/YunoHost ou le runtime Python 3.12 de recette ; le Python 3.9 Apple fourni sur ce poste ne l’expose pas).

## Consultation client — candidate 0.10.0

Depuis le projet, ouvrir **Consultation client**, puis confirmer **Publier la consultation**. Transmettre le lien et le code séparément. Le code généré est montré uniquement à sa création ; laisser son champ vide lors des publications suivantes pour le conserver. Une date de fin est facultative, et la révocation ferme les accès côté serveur immédiatement.

Le client consulte le fond complet et les annotations publiées, avec cartouche adapté aux équipes visibles, zoom de ×1 à ×50, déplacement et mesures temporaires. Le rechargement reprend la dernière publication. Les mesures ajoutées par le client ne sont jamais enregistrées dans le projet. Les mesures déjà publiées restent figées.

Seule la permission YunoHost `consultation` autorise les visiteurs, sur `/consultation` ; la permission principale et `/api/` restent authentifiées. Les fonds publiés sont conservés dans `data_dir/consultations` et sont inclus dans la sauvegarde existante. Leurs liens physiques évitent de recopier le même fond immuable à chaque publication ; un stockage séparé utilise une copie.

La recette complète du nouveau sous-chemin public, du SSO, des cookies HTTPS et du cycle sauvegarde/restauration reste obligatoire sur une instance isolée. La matrice de parcours est dans [CLIENT_CONSULTATION.md](.arcenal/CLIENT_CONSULTATION.md).

## Installation YunoHost

Le dépôt est un paquet YunoHost v2. Une installation de recette peut être lancée depuis l’administration YunoHost avec l’URL Git du dépôt. En ligne de commande sur une instance de test uniquement :

```sh
sudo yunohost app install https://github.com/arcenal-coder/arcenal-draw_ynh --debug
```

Avant une mise en production, vérifier le cycle installation, accès authentifié, import, calibrage, sauvegarde/reprise, export, mise à niveau, sauvegarde/restauration et suppression sur une instance YunoHost isolée.

La spécification fonctionnelle se trouve dans [`SPECIFICATION_POC.md`](SPECIFICATION_POC.md), l’historique dans [`HISTORIQUE_CONCEPTION.md`](HISTORIQUE_CONCEPTION.md) et les dernières preuves dans [`TEST_REPORT.md`](TEST_REPORT.md).
