# Livraison d'une première pipeline pour H3

Détection de compromissions à partir des journaux d'authentification Windows - focus sur les champs `SubjectUserName` et `TargetUserName`.

![](../miscellaneous/img/Pipeline_H3.png)


## Installation de l'environnement de travail
* Pour cloner le repo et installer l'environnement de travail, veuillez vous référer au [README.md](../README.md)

```
waad
└───notebooks/
    └───H1/
    └───H2/
    └───H3/
    └───H7/
    └───miscellaneous/
```

* Pour ouvrir un environnement pipenv avec jupyter lab :
```console
$ poetry shell
$ cd notebooks/
$ jupyter lab
```

* Faire tourner le notebook ``pipeline_H3.ipynb``.
</br>

## Phase 0 : Pré-traitement des noms de comptes
### 0.1
:inbox_tray: **Input**: Identifiants de l'instance PostgreSQL utilisée

:computer: **Process**: 
Récupération des combinaisons distinctes des champs `EventID`, `SubjectUserName`, `SubjectDomainName`, `SubjectUserSid`, `TargetUserName`, `TargetDomainName`, `TargetUserSid`.

:outbox_tray: **Output**: Un tableau contenant les combinaisons ci-dessus

</br>

### 0.2
:inbox_tray: **Input**: Les combinaisons ci-dessus.

:computer: **Process**: 
Sélection de tous les comptes dits **valides** selon les critères définis par l'analyste. Un nom de compte valide est un nom de compte (A,B) tel que :
   - il existe un événement 4624 pour lequel TargetUserName vaut A et TargetDomainName vaut B
   - il existe un événement 4624 pour lequel SubjectUserName vaut A et SubjectDomainName vaut B
   - il existe un événement 4672 pour lequel SubjectUserName vaut A et SubjectDomainName vaut B
   - il existe un événement 4634 pour lequel TargetUserName vaut A et TargetDomainName vaut B
   - il existe un événement 4648 pour lequel SubjectUserName vaut A et SubjectUserName vaut B

Il y a également la possibilité de construire un compte à partir des champs (TargetOutboundUserName, TargetOutboundDomainName). Mais tous sont-ils valides ou bien y a-t-il une définition similaire à ce que l'on a ci-dessus ?

:outbox_tray: **Output**: Une liste d'objets ``Account`` au format ``Asset`` défini dans la librairie, valides au sens des définitions ci-dessus.

</br>

### 0.3
:inbox_tray: **Input**: La liste de comptes valides au sens défini dans l'étape précédente.

:computer: **Process**: 
Sélection de tous les comptes avec un SID non standard ou non renseigné. Les SID non standards sont ceux qui commencent par 'S-1-5-21-*'. Cette étape préliminaire garantie un comptage plus juste des authentifications au cours du temps dans la partie 1.1.

:outbox_tray: **Output**: Une liste d'objets ``Account`` au format ``Asset`` défini dans la librairie, "valides" et avec des SID non-standards, garants de leur unicité.

</br>

### 0.4
Filtrage de tous les comptes ayant obtenus une session avec des privilèges 4672.

</br>

## Phase 1 : Recherche de Faits Notables
### 1.1.1
:inbox_tray: **Input**: La `Rule` souhaitée ainsi que les indicateurs à suivre.

:computer: **Process**: Nous filtrons les lignes du dataset selon la `Rule` et nous construisons un résumé des lignes valides avec au moins **asset_1**, **asset_2** et **systemtime**

Pour chaque compte, nous suivons plusieurs indicateurs au cours du temps : 

* Le nombre d'authentifications par jour
* Le nombre d'hôtes atteints par les connexions chaque jour
* Le nombre de nouveaux hôtes atteints chaque jour (par rapport aux ordinateurs déjà visités par ce compte dans le passé)
* Le nombre de connexions avec privilèges par jour (4672)

Dans une version ultérieure de H3 (en l'occurrence H7), on pourra s'intéresser aux **tentatives d'authentification** par nom de compte. 

:outbox_tray: **Output**: Des indicateurs temporels pour chaque compte sous forme d'objets ``TimeSeries``.

</br>

### 1.1.2
:inbox_tray: **Input**: Les indicateurs temporels pour chaque compte sous forme d'objets ``TimeSeries`` calculés précedemment.

:computer: **Process**: 
* Détection d'outliers (IQR) sur les indicateurs temporels calculés ci-dessus. La méthode IQR va chercher les points d'une série statistique qui sont loin en-dessous du premier quartile ou loin au-dessus du troisième quartile.

**Amélioration à apporter :**
Etant donnée la non uniformité des durées de logs conservés en mémoire par les hôtes, il arrive que certaines machines aient un comportement relativement calme pendant une longue durée puis une explosion sur la fin à cause de l'introductions massive de logs collectés sur certains DC. Cela se traduit par des alertes (faux positifs) sur les indicateurs. Un bon moyen d'éviter cela sera l'implémentation d'une méthode de détection IQR qui retranchera à l'indicateur sa tendance locale (ie indicateur - sa moyenne glissante sur une fenêtre de temps), pour ne conserver que les alertes "pics" locales. 

:outbox_tray: **Output**: Un ``FaitNotable`` par outlier détecté ci-dessus contenant le *compte* en question qui a un comportement changeant, un score et l'objet ``TimeSeries`` qui porte la trace d'un atypisme.

:microscope: **Remarque**:
* Les indicateurs n'ont pas tous la même pertinence, une alerte sur le nombre de connexions par jour arrivera plus souvent qu'une alerte sur le nombre de nouveaux hôtes visités par jour => des scores différents sont prévus dans le fichier [config.py](../../waad/utils/config.py). 
* Relever une alerte concordante sur les 3 indicateurs le même jour est particulièrement suspect, ce qui se traduit par l'attribution d'un score d'anormalité supplémentaire.

</br>

### 1.2.1 
:inbox_tray: **Input**: Les comptes valides isolés en 0.2.

:computer: **Process**: 
Pour chaque domaine, on regroupe les noms de comptes par préfixes et suffixes identiques.

:outbox_tray: **Output**: Cette étape produit une cartographie du parc à destination de l'analyste. Il ne s'agit pas pour l'instant de ``FaitsNotables``.

</br>

### 1.2.2
:inbox_tray: **Input**: Les comptes ayant obtenus une session à privilèges isolés en 0.3.

:computer: **Process**: 
Pour chaque domaine, on regroupe les noms de comptes par préfixes et suffixes identiques.

:outbox_tray: **Output**: Cette étape produit une cartographie du parc à destination de l'analyste. Il ne s'agit pas pour l'instant de ``FaitsNotables``.

</br>

## Phase 2
Les sorties sont des ``FaitNotable`` au sens défini par la [classe](../../waad/utils/fait_notable.py) correspondante dans la librairie. Chaque ``FaitNotable`` est structuré de la même manière avec un [``Account``](../../waad/utils/asset.py) au format [``Asset``](../../waad/utils/asset.py), une raison, un score d'anormalité et une trace de la méthode de détection utilisée pour conserver l'origine de l'erreur qui doit être visualisable par l'expert. Ils pourront être utilisés pour croiser les heuristiques en remontant des ``AnomalousAsset``.
