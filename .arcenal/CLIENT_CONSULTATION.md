# Consultation client — lot 0.10.0 Preview

## Exigences validées

Lien permanent sans compte YunoHost, protégé par code. Publication volontaire
d’un état figé du projet. Une actualisation charge la dernière publication.
Fond de plan complet, annotations, cartouche responsive, déplacement, zoom et
mesures locales temporaires uniquement. Aucun outil d’édition ni de calibrage.

## Parcours et droits

| Rôle | Déclencheur et écran | Données | Action et état de sortie | Preuve / notification |
| --- | --- | --- | --- | --- |
| Auteur authentifié | Bouton Consultation client dans l’éditeur | Son projet et son statut de partage | Confirme la publication ; reçoit lien et code initial | Date de publication et confirmation à l’écran |
| Auteur authentifié | Même dialogue | Sa publication | Republie sous le même lien, prolonge la date ou change le code | Confirmation ; changement de code invalide les sessions |
| Auteur authentifié | Révoquer, confirmation explicite | Son partage | Révocation du lien et de toutes ses sessions | Statut désactivé |
| Client extérieur | Lien, écran d’accès | Aucun plan avant code correct | Saisit le code ; ouvre la publication autorisée | Message générique si refus, date de publication si succès |
| Client autorisé | Vue plein écran | Fond complet, annotations et cartouche publié | Zoom, déplacement, cartouche, mesures temporaires | Aucune écriture dans les projets |
| Client autorisé | Actualisation du navigateur | Dernière publication | Recharge le plan et efface ses mesures temporaires | Date mise à jour |

Les rôles RH, candidat et autres profils métiers ne sont pas introduits dans
Crobard. Le propriétaire du projet est l’utilisateur authentifié par YunoHost.
Une publication ne contient ni identifiant du propriétaire ni projets voisins.

## Architecture et sécurité

- Interface publique dédiée sous `/consultation/`, permission YunoHost visiteurs
  limitée à ce sous-chemin ; l’éditeur et `/api/` restent authentifiés.
- SQLite : partages par propriétaire/projet, révisions figées, sessions hachées
  et compteurs d’accès communs aux workers. Copies des fonds sous `data_dir` :
  supprimer une base de travail ne casse pas une consultation publiée.
- Code stocké avec sel et scrypt ; lien aléatoire, session aléatoire HttpOnly,
  Secure, SameSite=Strict, durée maximale huit heures. Limitation des essais de
  code par partage/adresse et globalement par adresse. Aucun code dans l’URL.
- Toute lecture du plan ou d’une révision vérifie session, partage actif et
  échéance. Les seules routes publiques sont les lectures et l’ouverture/fermeture
  d’une session. Les routes d’édition conservent le contrôle propriétaire.
- SVG des annotations reconstruit par liste blanche, sans script, style actif,
  lien externe ou fichier arbitraire. Images intégrées PNG/JPEG bornées.
- Publication explicite, révocation confirmée ; réponses privées `no-store` et
  absence de journaux d’accès sur l’API de consultation.
- Données nouvelles additives, comprises dans la sauvegarde `data_dir` existante.
  Aucune migration destructive ni opération sur des données de production.

## Recette attendue

Auteur : publier, copier lien/code, modifier sans publier, republier et vérifier
le même lien, modifier le code, révoquer. Autre auteur : aucune gestion du partage.
Client : code incorrect refusé, zoom/pan/mesure, rechargement sur nouvelle version,
aucune modification serveur, accès expiré/révoqué refusé, aucune lecture d’un autre
plan ni accès à l’éditeur. Installation et recette YunoHost restent à exécuter
sur une instance isolée avant ouverture extérieure.
