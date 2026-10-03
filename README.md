# ARCenal DRAW — POC de validation

Ouvrez `index.html` dans un navigateur moderne.

Le POC permet de valider l'accueil, les bases réutilisables, la calibration, un cartouche à une société par défaut extensible si nécessaire, les calculs Se-75/Ir-192, le placement des zones, leur fusion exacte et leur dissociation, l'échelle métrique, l'orientation A3, la sauvegarde locale et l'export par impression PDF.

La synthèse fonctionnelle complète se trouve dans `SPECIFICATION_POC.md`.

Le PDF est le format de travail interne. Un PDF importé reste natif et est lu progressivement avec PDF.js, sans conversion PNG. Les DXF sont convertis en PDF vectoriel ; les DWG suivent la même chaîne après conversion géométrique minimale par `dwg2dxf`. Les matériaux, styles de tableaux et autres objets AutoCAD décoratifs instables n'empêchent pas l'import lorsqu'un DXF exploitable a bien été produit. PNG et JPEG restent acceptés pour les plans scannés. Tous les originaux sont conservés.

## Socle serveur

Le dépôt contient désormais une application WSGI Python volontairement minimale :

- SQLite pour les projets, archives et métadonnées de fichiers ;
- Gunicorn derrière Nginx ;
- authentification issue des en-têtes SSO YunoHost ;
- dépôt limité à 100 Mo et restreint aux formats DWG, DXF, PDF, PNG et JPEG ;
- sauvegarde locale du navigateur conservée comme mode de secours ;
- synchronisation automatique vers l'API lorsque l'application est servie en HTTP(S).

## Installation YunoHost

Le répertoire constitue un paquet YunoHost v2 local. Depuis l'administration YunoHost, utiliser « Installer une application personnalisée » avec l'URL Git du dépôt. En ligne de commande :

```sh
sudo yunohost app install https://URL_DU_DEPOT_GIT --debug
```

L'application installe Nginx, Gunicorn, PDF.js, ezdxf, librsvg, GNU LibreDWG 0.13.3, le service `arcenal_draw` et son répertoire de données sauvegardable. LibreDWG est compilé automatiquement pour l'architecture du serveur pendant l'installation ou la mise à jour ; aucune installation manuelle de `dwg2dxf` n'est nécessaire.

## Vérifications locales

```sh
PYTHONPYCACHEPREFIX=/tmp/arcenal-pycache python3 -m unittest discover -s tests -v
bash -n scripts/*
```
