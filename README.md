# ARCenal DRAW — POC de validation

Ouvrez `index.html` dans un navigateur moderne.

Le POC permet de valider l'accueil, les bases réutilisables, la calibration, un cartouche à une société par défaut extensible si nécessaire, les calculs Se-75/Ir-192, le placement des zones, leur fusion exacte et leur dissociation, l'échelle métrique, l'orientation A3, la sauvegarde locale et l'export par impression PDF.

La synthèse fonctionnelle complète se trouve dans `SPECIFICATION_POC.md`.

La conversion DWG/DXF/PDF et l'affichage des images de plan restent simulés jusqu'au raccordement complet du convertisseur. Les PDF, PNG et JPEG suivent néanmoins dès maintenant le parcours de calibration obligatoire.

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

L'application installe Nginx, Gunicorn, le service `arcenal_draw` et son répertoire de données sauvegardable. La conversion LibreDWG est détectée si `dwgread` est présent ; son installation reproductible sera ajoutée après validation sur les architectures cibles.

## Vérifications locales

```sh
PYTHONPYCACHEPREFIX=/tmp/arcenal-pycache python3 -m unittest discover -s tests -v
bash -n scripts/*
```
