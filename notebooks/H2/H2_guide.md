# Pipeline pour H2

Détection de compromissions à partir des journaux d'authentification Windows - focus sur le champ WorkstationName

![](../miscellaneous/img/Pipeline_H2.png)


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

* Faire tourner le notebook ``pipeline_H2.ipynb``.

</br>

## Phase 0 : Pré-traitement des noms de machines
### 0.1
:inbox_tray: **Input**: Identifiants de l'instance PostgreSQL utilisée

:computer: **Process**: 
* Récupération des éléments distincts des champs *WorkstationName* et *Host*. 
* Construction des objets ``Machine`` correspondants au format ``Asset`` avec nom de domaine associé. Les paramètres `host_machine_maker` et `workstation_machine_maker` permettent d'appliquer des pré-traitements (voir doc Sphinx)
:outbox_tray: **Output**: Des objets ``Machine`` contenant les noms de machine et les domaines associés, triés selon leur colonne de provenance *WorkstationName* ou *Host*.

</br>

## Phase 1 : Recherche de Faits Notables
Il est nécessaire de souligner que le champ WorkstationName contient parfois la machine source de l'authentification et parfois la machine destination. Nous considérons qu'il s'agit de la machine source justement quand WorkstationName est différent de Host.

### 1.1.1
:inbox_tray: **Input**: Une `Rule` définie par l'analyste.

:computer: **Process**: Pour chaque *WorkstationName*, nous requêtons les événements  d'authentifications associés et nous filtrons ceux pour lesquels *WorkstationName* != *Host* (selon la `Rule` définie). Nous proposons donc de chercher si des machines changent de comportement de manière significative par rapport à leur modèle légitime. Pour cela, nous suivons plusieurs indicateurs au cours du temps : 

* Le nombre d'authentifications par jour
* Le nombre d'hôtes atteints par les connexions chaque jour
* Le nombre de nouveaux hôtes atteints chaque jour (par rapport aux ordinateurs déjà visités par cette *WorkstationName* dans le passé)

:outbox_tray: **Output**: Des indicateurs temporels pour chaque *WorkstationName* sous forme d'objets ``TimeSeries``.

:microscope: **Remarque**: Dans le jeu de données anonymisé, les WorkstationName semblent toutes être des *machine_name* alors que les Host sont de la forme *machine_name.domain*.

</br>

### 1.1.2
:inbox_tray: **Input**: Les indicateurs temporels pour chaque *WorkstationName* != *Host* sous forme d'objets ``TimeSeries`` calculés précedemment.

:computer: **Process**: 
* Détection d'outliers (IQR) sur les indicateurs temporels calculés ci-dessus. La méthode IQR va chercher les points d'une série statistique qui sont loin en-dessous du premier quartile ou loin au-dessus du troisième quartile.

**Amélioration à apporter :**
Etant donnée la non uniformité des durées de logs conservés en mémoire par les hôtes, il arrive que certaines machines aient un comportement relativement calme pendant une longue durée puis une explosion sur la fin à cause de l'introductions massive de logs collectés sur certains DC. Cela se traduit par des alertes (faux positifs) sur les indicateurs. Un bon moyen d'éviter cela sera l'implémentation d'une méthode de détection IQR qui retranchera à l'indicateur sa tendance locale (ie indicateur - sa moyenne glissante sur une fenêtre de temps), pour ne conserver que les alertes "pics" locales. 

:outbox_tray: **Output**: Un ``FaitNotable`` par outlier détecté ci-dessus contenant la *WorkstationName* en question qui a un comportement changeant, un score et l'objet ``TimeSeries`` qui porte la trace d'un atypisme.


:microscope: **Remarque**:
* Les indicateurs n'ont pas tous la même pertinence, une alerte sur le nombre de connexions par jour arrivera plus souvent qu'une alerte sur le nombre de nouveaux hôtes visités par jour => des scores différents sont prévus dans le fichier [config.py](../../waad/utils/config.py). 
* Relever une alerte concordante sur les 3 indicateurs le même jour est particulièrement suspect, ce qui se traduit par l'attribution d'un score d'anormalité supplémentaire.

</br>

### 1.2.1
:inbox_tray: **Input**: *WorkstationName* et *Host*.

:computer: **Process**: 
On regroupe les noms de machines par préfixes et les suffixes identiques. Il est également possible d'effectuer ce clustering par domaine, pour mieux se rendre compte des différents domaines du parc.

:outbox_tray: **Output**: Cette étape produit une cartographie du parc à destination de l'analyste, pas encore des ``FaitsNotables``.

</br>

### 1.2.2
:inbox_tray: **Input**: Combinaisons distinctes de *WorkstationName* et *logontype* ainsi que *Host*. 

:computer: **Process**: 
Application du clustering très spécifique tel que défini avec l'ANSSI.
* On regroupe les noms de machines sur les préfixes et les suffixes qui existent dans le jeu de données. Il est également possible d'effectuer ce clustering par domaine, pour mieux se rendre compte des différents domaines du parc.
* On retire les *WorkstationName* ayant un *logontype* 2 ou 11 car cela veut dire qu'un utilisateur s'est connecté à cette machine en présentiel et que ce n'est donc pas la machine d'un attaquant.

:outbox_tray: **Output**: Un dictionnaire *clusters* contenant les groupes de machines constitués.

</br>

### 1.2.3
:inbox_tray: **Input**: Le dictionnaire *clusters* obtenu dans l'étape précédente.

:computer: **Process**: 
* Les clusters de grosse taille (paramétrable, par défaut > 50), sont écartés et ne constituent pas de ``FaitNotable``
* Les clusters de taille moyenne (paramétrable, par défaut entre 7 et 50) sont traités de la manière suivante :
    - si le ratio d'hosts présents dans le cluster est supérieur à une certaine valeur (paramétrable), alors les WorkstationName sont probablement des machines du parc qui n'ont pas été collectées et ne sont donc pas suspectes d'un point de vue de leur nomenclature
    - sinon elles sont considérées comme des ``FaitNotable`` avec un score associé
* Les *WorkstationName* dans des clusters de petite taille sont directement considées comme suspecte et un ``FaitNotable`` leur est associé
* Les *WorkstationName* ayant un nom commençant par 'WIN*' ou 'DESKTOP*' sont traitées séparément pour former des ``FaitNotable`` avec un score d'anormalité supplémentaire. En effet, il s'agit souvent de noms donnés par défaut à des machines Windows qui sont plus susceptibles d'être des machines d'attaquants.

:warning: Puisque l'information nom de domaine n'est pas présente dans le raisonnement ci-dessus (issue d'un clustering sur les noms de machine), tous les assets dont le nom de machine correspond sont considérés dans le ``FaitNotable`` et un score leur est imputé. On peut améliorer cela en effectuant un clustering par domaine.

:outbox_tray: **Output**: Des ``FaitNotable`` sur les *WorkstationName* construits selon les raisonnements ci-dessus. Chaque ``FaitNotable`` contient une *WorkstationName*, une phrase d'explications (*raison*) et un score défini dans le fichier [config.py](../../waad/utils/config.py).

</br>
</br>

## Phase 2
Les sorties sont des ``FaitNotable`` au sens défini par la [classe](../../waad/utils/fait_notable.py) correspondante dans la librairie. Chaque ``FaitNotable`` est structuré de la même manière avec une ``Machine`` au format [``Asset``](../../waad/utils/asset.py), une raison, un score d'anormalité et une trace de la méthode de détection utilisée pour conserver l'origine de l'erreur qui doit être visualisable par l'expert. Ils pourront être utilisés pour croiser les heuristiques en remontant des ``AnomalousAsset``.