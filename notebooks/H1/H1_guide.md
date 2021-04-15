# Livraison d'une première pipeline pour H1

Détection de compromissions à partir des journaux d'authentification Windows - focus sur les IP

![](../miscellaneous/img/Pipeline_H1.png)


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

* Dans un terminal, sous un environnement Poetry, faire tourner le notebook ``Database.ipynb`` pour remplir votre instance PostgreSQL avec vos données.

* Faire tourner le notebook ``pipeline_H1.ipynb``.


## Phase 0 : Pré-traitement sur les IP
### 0.0 
:inbox_tray: **Input**: Identifiants de l'instance PostgreSQL utilisée

:computer: **Process**: Récupération de l'ensemble des adresses IPs distinctes (colonne *IPAddress*)

:outbox_tray: **Output**: Toutes les valeurs distinctes d'IP.

</br>

### 0.1
:inbox_tray: **Input**: Des IP au format `str` issues de la colonne ``ipaddress`` du dataset. 

:computer: **Process**: Filtrage des IPv4 et des IPv6 par application de la librairie ``ipaddress``. Classification entre public et privée avec la librairie ``ipaddress``.

:outbox_tray: **Output**: Plusieurs groupes d'IP, *ipv4s*, *private_ipv4s*, *public_ipv4s*, *loopback_ipv4s*, *ipv6s*, *private_ipv6s*, *public_ipv6s*, *loopback_ipv6s* et *others*.

</br>

### 0.3.1
Filtrage des IP publiques (IPv4 et IPv6) selon les règles définies par <https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml> (librairie *ipaddress*).

</br>

### 0.3.2
Filtrage des IP privées (IPv4 et IPv6) avec la librairie *ipaddress* (selon les mêmes règles que ci-dessus).

</br>

### 0.2 et 0.4
Calcul du ratio nombre d'IPv6 sur nombre d'IP distinctes du dataset. Si le ratio d'IPv6 est très faible (paramètre à définir, par défaut 2%), alors les IPv6 sont remontées comme faits notables.

</br>


## Phase 1 : Recherche de Faits Notables
On distingue 2 types  d'**assets**:
* ceux qui sont subtilisables par les attaquants comme les machines du parc informatique (et donc les IP privées), les comptes utilisateurs... Pour eux, on cherche des comportements anormaux de ces ``assets`` par rapport à leur modèle légitime (suivi d'indicateurs pertinents au cours du temps et détection d'anomalies à partir de cela). Ex : 1.3 

* ceux qui sont directement suspects de par leur nature (comme les IP publiques). Dans ce cas, on cherche plutôt des cas qui se distinguent significativement des autres sur des indicateurs pertinents également. Ex : méthode KMeans laissée de côté pour l'instant.


### 1.1.1
Il arrive que l'entité étudiée possède une série d'IP publiques qui communiquent régulièrement avec le parc. Les IP suspectes sont plutôt celles qui sont isolées des autres. Pour cela, on cherche à former des groupes d'IP en fonction de leur proximité et leur densité.

:inbox_tray: **Input**: L'ensemble des IP publiques (IPv4 et IPv6 confondues). 

:computer: **Process**: Application d'un algorithme de clustering DBSCAN sur les IP exprimées en entiers, avec la métrique usuelle sur l'ensemble des entiers naturels **N**. Chaque cluster a un titre qui correspond au plus grand préfixe commun de toutes les IP contenu dans ce cluster (ex : 192.168.2.0/24).

:outbox_tray: **Output**: Des groupes d'IP denses et suffisamment proches les unes des autres. Le cluster ``None``, regroupe toutes les adresses IP atypiques.

</br>

### 1.1.2
:inbox_tray: **Input**: L'ensemble des IP publiques outliers (du groupe None) du clustering précédent et qui possèdent au moins un 4624. 

:computer: **Process**: Sur ces IP isolées, on fait tourner l'analyse de tuples version analystes c'est à dire la recherche de regroupements de connexions rares en sélectionnant un nombre fini de champs. Les champs à explorer peuvent être fournis en tant que paramètres, par défaut, ceux contenus dans ``TupleAnalysisFields``du fichier [constants.py](../../waad/utils/constants.py) sont utilisés. On considère qu'on a un groupement rare si :
* Le nombre de groupes trouvé est faible (paramétrable, pour l'instant 10)
* Il existe un groupement d'authentifications de cardinal **n1** très faible devant le cardinal du groupe de connexions majoritaires **n2** (ie n1 < min(0.05 * n2, 50)). Le paramètre 5% sera paramétrable par la suite.

:warning: Cette étude de tuple devra être retravaillée suite aux retours de l'expert ANSSI à ce sujet.

:outbox_tray: **Output**: Des ``FaitsNotables`` qui contiennent une IP publique isolée en terme de distance avec au moins un groupement rare pour la caractériser et un score tel que défini dans [config.py](../../waad/utils/config.py). 

</br>

### 1.2
</br>

### 1.2.1
:inbox_tray: **Input**: Une `Rule` définie par l'analyste.

:computer: **Process**: Le champ *IpAddress* correspond à la source de l'authentification, nous proposons donc de chercher si des IP changent de comportement de manière significative par rapport à leur modèle légitime. Pour cela, nous suivons plusieurs indicateurs au cours du temps (selon la `Rule` et les `Indicator` définis) : 

* Le nombre d'authentifications par jour
* Le nombre d'hôtes atteints par les connexions chaque jour 
* Le nombre de nouveaux hôtes atteints chaque jour (par rapport aux ordinateurs déjà visités par ce compte dans le passé)

:outbox_tray: **Output**: Des indicateurs temporels pour chaque IP privée sous forme d'objets ``TimeSeries``.

</br>

### 1.2.2
:inbox_tray: **Input**: Les indicateurs temporels pour chaque IP privée sous forme d'objets ``TimeSeries`` calculés précedemment.

:computer: **Process**: 
* Détection d'outliers (IQR) sur les indicateurs temporels calculés ci-dessus. La méthode IQR va chercher les points d'une série statistique qui sont loin en-dessous du premier quartile ou loin au-dessus du troisième quartile.

**Amélioration à apporter :**
Etant donnée la non uniformité des durées de logs conservés en mémoire par les hôtes, il arrive que certaines IP aient un comportement relativement calme pendant une longue durée puis une explosion sur la fin à cause de l'introductions massive de logs collectés sur certains DC. Cela se traduit par des alertes (faux positifs) sur les indicateurs. Un bon moyen d'éviter cela sera l'implémentation d'une méthode de détection IQR qui retranchera à l'indicateur sa tendance locale (ie indicateur - sa moyenne glissante sur une fenêtre de temps), pour ne conserver que les alertes "pics" locales. 

:outbox_tray: **Output**: Un ``FaitNotable`` par outlier détecté ci-dessus contenant l'IP publique en question qui a un comportement changeant, un score et l'objet ``TimeSeries`` qui porte la trace d'un atypisme.


:microscope: **Remarque**:
* Les indicateurs n'ont pas tous la même pertinence, une alerte sur le nombre de connexions par jour arrivera plus souvent qu'une alerte sur le nombre de nouveaux hôtes visités par jour => des scores différents sont prévus dans le fichier [config.py](../../waad/utils/config.py). 
* Relever une alerte concordante sur les 3 indicateurs le même jour est particulièrement suspect, ce qui se traduit par l'attribution d'un score d'anormalité supplémentaire.

</br>

### 1.2.3
:inbox_tray: **Input**: Les IP privées du dataset.

:computer: **Process**: 
On applique un algorithme de clustering DBSCAN de la librairie sklearn sur les IP privées pour les grouper par sous-réseau et chercher des outliers en termes de nomenclature. 
* On raisonne sur l'ensemble des IPv4 et IPv6 en valeurs décimales
* On cherche des clusters denses dans l'ensemble des entiers naturels.

:outbox_tray: **Output**: Un dictionnaire 'clusters' qui groupe les IP ensemble si elles forment un cluster suffisamment dense en termes de proximité au sens de la distance cartésienne sur les entiers. En affichant le résultat, on obtient une cartographie des groupes d'IP dans le parc. Il ne s'agit en revanche pas de ``FaitNotable`` (à moins de rajouter des règles métiers). 

</br>
</br>

## Phase 2
Les sorties sont des ``FaitNotable`` au sens défini par la [classe](../../waad/utils/fait_notable.py) correspondante dans la librairie. Chaque ``FaitNotable`` est structuré de la même manière avec une IP au format [``Asset``](../../waad/utils/asset.py), une raison, un score d'anormalité et une trace de la méthode de détection utilisée pour conserver l'origine de l'erreur qui doit être visualisable par l'expert. Ils pourront être utilisés pour croiser les heuristiques en remontant des ``AnomalousAsset``.
