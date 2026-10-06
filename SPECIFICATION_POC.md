# ARCenal DRAW — synthèse fonctionnelle du POC

## Principe directeur

La feuille visible est la source de vérité du rendu. Le zoom d'affichage ne modifie pas le document. Le zoom du plan dans la feuille modifie sa correspondance métrique et recalcule immédiatement l'échelle graphique du cartouche.

## Démarrage et bases de plans

- Accueil avec projets récents et bases de plans déjà converties.
- Import par sélection ou glisser-déposer d’un fichier PDF, PNG ou JPEG.
- Conservation du fichier original.
- Conversion future vers une géométrie interne vectorielle normalisée en mètres.
- Création de plusieurs projets annotés à partir d'une même base propre.

Les PDF vectoriels sont convertis en SVG. Les PDF scannés et les images restent affichés dans leur format natif.

## Calibration

- Lecture automatique de l'unité déclarée quand elle est fiable.
- Unité interne systématique : mètre.
- Si l'unité est absente : calibration par deux points et saisie d'une distance réelle en mètres.
- Pour un PDF ou une image, cette calibration est obligatoire à la première ouverture du document. La distance de référence est saisie dans la fenêtre de calibration et pourra être corrigée ultérieurement.
- Recalibration ultérieure disponible.
- Une modification de calibration ne modifie jamais rétroactivement un PDF déjà exporté.

## Interventions radiologiques

Le cartouche commence avec une seule société. L'utilisateur peut volontairement l'étendre jusqu'à dix interventions au moyen d'un sélecteur compact « moins / saisie numérique / plus ». Chaque intervention possède :

- un code A à E et une couleur ;
- une société ;
- un radionucléide, Se-75 ou Ir-192 ;
- une activité saisissable en Ci ou TBq ;
- une atténuation 1/250, activée par défaut ;
- une plage horaire de tirs, par exemple de 00h00 à 04h00 ;
- un surbalisage optionnel propre à l'équipe : distance exacte depuis le point d'impact, couleur, épaisseur et trait continu ou pointillé ;
- les distances calculées pour 2,5 µSv/h et 25 µSv intégrés sur une heure.

Hypothèse retenue : émission continue pendant une heure, sans saisie de temps d'exposition.

Constantes utilisées dans le POC :

- Se-75 : 55 000 µSv/h par TBq à 1 m ;
- Ir-192 : 130 000 µSv/h par TBq à 1 m.

Calcul : `rayon = racine((constante × activité TBq) / (seuil × atténuation))`, avec une atténuation égale à 250 ou 1.

## Placement des zones

1. Choisir l'outil Point d'impact.
2. Choisir l'intervention.
3. Choisir le seuil 2,5 µSv/h, 25 µSv sur une heure, ou « Réglage manuel ».
4. Pour un calcul radiologique, conserver ou décocher l'atténuation 1/250. Pour un réglage manuel, saisir directement le rayon demandé par le client en mètres.
5. Cliquer sur le point d'impact.

Le cercle adopte le rayon réel calculé ou la distance contractuelle saisie manuellement. Le mode manuel ne modifie pas les résultats radiologiques calculés dans le cartouche. Un petit trèfle radiologique est placé au centre. Deux cercles déposés au même point partagent visuellement le même symbole.

Si le surbalisage de l'équipe est coché, un cercle supplémentaire est créé automatiquement autour de chacun de ses points d'impact. Sa distance est absolue : une saisie de 50 m trace un rayon de 50 m depuis l'impact, et non 50 m ajoutés au rayon radiologique. Son intérieur reste transparent. Son contour possède sa propre couleur et peut être continu ou pointillé. Il peut être sélectionné et masqué avec la corbeille sans supprimer le point d'impact ni sa zone radiologique.

Lorsque plusieurs zones radiologiques sont fusionnées, leurs surbalisages sont fusionnés en concordance. Le contour résultant reprend uniquement les arcs extérieurs exacts des surbalisages correspondants. La dissociation des zones radiologiques restitue également les surbalisages individuels.

## Fusion et dissociation

- La fusion est limitée aux zones d'une même intervention.
- Les zones doivent se toucher.
- Le contour fusionné est composé des arcs extérieurs exacts des cercles : aucune enveloppe convexe et aucun lissage déformant.
- Les cercles sources restent enregistrés.
- L'action Dissocier les zones restaure les cercles d'origine.

## Cartouche et échelle

- Titre : « Plan de contrôle gammagraphique ».
- Premier encart sous le titre : date saisissable du plan.
- Champ « Localisation » modifiable directement dans la partie Cartouche, immédiatement sous la date ; cette valeur alimente aussi le cartouche imprimé et le nom du PDF.
- Logo de société affiché dans un encart séparé, juste au-dessus du bandeau gris du cartouche.
- Import du logo depuis les paramètres en PNG ou JPEG, avec redimensionnement et sauvegarde dans le projet.
- Le dépôt PDF est présenté dans le POC ; sa conversion graphique sera assurée par le futur backend.
- Cartouche étroit, ancré en bas à droite et extensible vers le haut.
- Pour chaque intervention, le cartouche n'affiche que le dernier type de balisage effectivement sélectionné — 2,5 µSv/h, 25 µSv/1h ou manuel — et sa distance associée.
- La mention « Surbalisage de sécurité » et sa distance restent totalement absentes lorsque l'option n'est pas activée.
- Le logo est posé librement au-dessus du cartouche, sans encadré, aligné sur son montant gauche et accompagné de l'intitulé du client.
- Une ligne compacte par intervention.
- La liste est contextuelle au cadrage : seules les équipes possédant au moins une zone de tir visible dans la feuille au zoom et au déplacement courants apparaissent. Si aucun impact n'a encore été créé, les équipes configurées restent affichées.
- L'horaire des tirs et, s'il est actif, le surbalisage de chaque intervention sont affichés avec son style et sa distance.
- Échelle graphique exclusivement exprimée en mètres.
- Valeurs lisibles selon une progression 1, 2, 5, 10, 20, 50, etc.
- Adaptation automatique au zoom réel du plan, sans réaction au zoom d'affichage de l'interface.
- Dernier encart sous l'échelle : « Réalisé par », avec nom, prénom, fonction et signature.
- Encart optionnel « Validé par », activable dans les paramètres avec les mêmes informations.
- Signatures PNG/JPEG intégrées directement ; dépôt PDF préparé pour la conversion par le futur backend.

## Navigation et signalisation

- Les paramètres s'ouvrent dans une fenêtre modale centrée, avec un bouton de fermeture explicite.
- Zoom du plan à la molette, centré sur la position du pointeur.
- Déplacement du fond de plan par glisser-déposer avec l'outil Sélection.
- Palette de signalement : panneau de barrage, balisage flash, barrière et cône.
- Les équipements placés sont sélectionnables, enregistrés et supprimables.
- La corbeille de la barre d'outils supprime un cercle, une zone fusionnée complète ou un équipement sélectionné.
- Les touches Retour arrière et Supprimer exécutent la même suppression lorsque aucun champ n'est en cours de saisie.
- Un point d'impact ou une zone sélectionnée peut être réattribué à une autre société/équipe ; sa couleur et son calcul sont alors actualisés depuis le cartouche.
- Les actions « Fusionner » et « Dissocier » restent masquées tant que la sélection courante ne permet pas réellement de les utiliser.

## Sauvegarde et export

- Sauvegarde locale automatique après chaque modification significative.
- Conservation des cercles, zones fusionnées, interventions, couleurs, calibration, orientation et zoom du plan.
- Sauvegarde forcée avant l'impression PDF.
- Nom d'export automatique : `AAAA.MM.JJ plan radio CLIENT localisation`.
- Chaque export crée une archive locale réouvrable depuis l'accueil ; le POC conserve les douze exports les plus récents.
- Export basé sur le même SVG que la feuille visible.
- L'impression est contrainte à une unique feuille A3, sans page vierge préalable.

## Limites volontaires du POC

- Les PDF vectoriels sont convertis en SVG ; les PDF scannés sont lus progressivement par PDF.js ; les PNG et JPEG restent natifs. Aucun format n’est converti en PNG intermédiaire.
- La sélection graphique directe des deux points reste à ajouter ; la version actuelle demande la distance mesurée et la distance réelle dans la fenêtre de calibration.
- Le stockage serveur, SQLite et le SSO YunoHost ne sont pas encore connectés.
