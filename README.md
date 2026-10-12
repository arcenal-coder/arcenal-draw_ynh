# ARCenal DRAW

ARCenal DRAW est une application YunoHost de conception de plans d’impact radiologique. Elle importe des fonds PDF, PNG ou JPEG, permet leur calibrage métrique, ajoute les zones de balisage, conserve des instantanés d’export réouvrables et produit un export PDF WYSIWYG par la fonction d’impression du navigateur.

## Architecture

- interface statique HTML, CSS et JavaScript sans framework ;
- API WSGI Python servie par Gunicorn derrière Nginx ;
- authentification transmise par le SSO YunoHost ;
- SQLite pour les projets, instantanés d’export et métadonnées ;
- Poppler pour convertir la première page des PDF vectoriels en SVG ;
- PDF.js embarqué pour l’affichage progressif des PDF restant natifs.

Les données persistantes sont placées dans `/var/lib/arcenal_draw` par la ressource `data_dir` YunoHost. Les formats CAO natifs ne font pas partie du périmètre.

## Vérifications locales

Depuis la racine du dépôt :

```sh
PYTHONPYCACHEPREFIX=/tmp/arcenal-draw-pycache python3 -m py_compile backend/*.py
node --check app.js
bash -n scripts/*
PYTHONPYCACHEPREFIX=/tmp/arcenal-draw-pycache python3 -m unittest discover -s tests -v
git diff --check
```

Il n’existe ni dépendance Python installée par `pip`, ni compilation frontend, ni étape de build. Le paquet s’appuie uniquement sur les paquets APT déclarés dans `manifest.toml` et sur les fichiers statiques versionnés.

## Installation YunoHost

Le dépôt est un paquet YunoHost v2. Une installation de recette peut être lancée depuis l’administration YunoHost avec l’URL Git du dépôt. En ligne de commande sur une instance de test uniquement :

```sh
sudo yunohost app install https://github.com/arcenal-coder/arcenal-draw_ynh --debug
```

Avant une mise en production, vérifier le cycle installation, accès authentifié, import, calibrage, sauvegarde/reprise, export, mise à niveau, sauvegarde/restauration et suppression sur une instance YunoHost isolée.

La spécification fonctionnelle se trouve dans [`SPECIFICATION_POC.md`](SPECIFICATION_POC.md), l’historique dans [`HISTORIQUE_CONCEPTION.md`](HISTORIQUE_CONCEPTION.md) et les dernières preuves dans [`TEST_REPORT.md`](TEST_REPORT.md).
