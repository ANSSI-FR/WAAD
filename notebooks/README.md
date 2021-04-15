# Guide d'utilisation

Ce dossier comporte un sous-dossier par heuristique, contenant pour chacune le notebook du chaînage et la documentation associée. La suite de ce document est dédiée à des explications plus générales, sur le croisement des heuristiques et la remontée des faits notables. 

```
waad
└───notebooks/
    └───H1/
        |   pipeline_H1.ipynb
        |   H1_guide.md
    └───H2/
    └───H3/
    └───H7/
    └───miscellaneous/
        └───archives/
        └───img/
        └───prototypes/
            |   .gitkeep
        |   Database.ipynb
```

## Définitions

* **Fait Notable** : un fait notable est une rareté relevée dans les authentifications d'un dataset. Il ne s'agit pas forcément d'une conséquence du passage d'un pirate mais parfois simplement d'un "symptôme" du jeu de données en question, provenant des choix faits dans le parc informatique.

* **Asset** : un asset est un terme générique qui représente une entité du dataset (IP, machine ou compte utilisateur). Leur comportement peut porter les traces d'une éventuelle attaque. Nous allons chercher à isoler ceux qui sont les plus suspects.


## Faits Notables

Document d'explications concernant la classe [``FaitNotable``](../waad/utils/fait_notable.py) et la gestion des scores associés.

### Classe FaitNotable
```
FaitNotable
    anomaly_score: float
    reason: str
    assets_concerned: List[Asset]
    content: Optional[None]
```

* **anomaly_score**: Score d'anormalité qui qualifie l'importance du ``FaitNotable``. Ce dernier est attribué à la construction de l'objet, par défaut des scores sont prévus selon le type d'anomalie dans le fichier [``config.py``](../../waad/utils/config.py)
* **reason**: Phrase d'explication / raison pour laquelle ce fait est remonté aux analystes (voir les faits notables construits ci-dessous)
* **assets_concerned**: Les assets (au format [``Asset``](../../waad/utils/asset.py) concernés par le fait notable remonté.
* **content**: Contenu additionnel pour aider l'investigateur. Si ce n'est pas ``None``, l'objet doit implémenter la méthode display() pour afficher un élément d'interprétation.

* **display()** méthode qui appelle la méthode display() de **content** si elle existe. Si ce n'est pas le cas, elle affiche simplement l'élément **content**.


## ComputeFaitsNotables
Pour chaque heuristique on applique des méthodes de détection qui permettent de générer des alertes. Ces dernières sont associées a des assets spécifiques du parc et à partir d'elles on va générer des alertes avec un formalisme commun, qui est celui de FaitNotable. Les faits notables sont pondérés par leur degré d'importance et contiennent des éléments d'explications.

La classe [``ComputeFaitsNotables``](../../waad/utils/fait_notable.py) est une classe mère composées de la manière suivante : 

```
ComputeFaitsNotables
    config: Dict[str, Dict[str, float]]
    faits_notables: List[FaitNotable]
```

La méthode run() de la classe mère permet d'accéder au dictionnaire qui contient les scores et qui est stocké dans [``config.py``](../../waad/utils/config.py). Les classes filles héritant de ComputeFaitsNotables sont :

* ComputeFaitNotablesFromRareIPv6
* ComputeFaitNotablesFromIndicators
* ComputeFaitNotablesFromIsolatedMachine
* ComputeFaitNotablesFromWINMachine
* ComputeFaitNotablesFromDESKTOPMachine
* ComputeFaitNotablesFromAnalystTuplesAnalysers
* ...

Les classes filles devront réimplémenter la méthode run() afin de remplir la liste ``faits_notables`` à partir des anomalies détectées par les différentes méthodes mises en place dans la librairie. Toutes les classes filles ont la même structure via l'héritage et sont dans le même fichier pour l'instant et une description de chacune est proposée ci-dessous. 


### ComputeFaitNotablesFromRareIPv6
Calcul du ratio nombre d'IPv6 sur nombre d'IP distinctes du dataset. Si ce ratio est inférieur à un seuil paramétrable et par défaut égal à 2%, alors l'usage d'IPv6 est considéré comme rare et des faits notables sont remontés pour chaque. 

* **anomaly_score**: Le score par défaut prévu dans [``config.py``](../../waad/utils/config.py) est de 0.7
* **reason**: Low ratio of IPv6
* **assets_concerned**: Chaque ipv6 si le ratio est faible
* **content**: ``None``


### ComputeFaitNotablesFromAnalystTuplesAnalysers
Après avoir fait tourné une analyse de tuples, si l'on découvre des associations rares, on crée des faits notables pour les assets associés.

* **anomaly_score**: Le score par défaut prévu dans [``config.py``](../../waad/utils/config.py) est de 0.9 (le plus important attribué individuellement)
* **reason**: *asset_name* with rare grouping of events
* **assets_concerned**: Chaque asset rencontré dans le tuple rare
* **content**: Un tableau pandas, résumé de l'analyse de tuple effectuée


### ComputeFaitNotablesFromIndicators
Après avoir calculé des indicateurs au format ``StatSeries`` ou ``TimeSeries`` on fait tourner une détection d'anomalies sur nos indicateurs. Si des comportements suspects sont remontés, des faits notables sont créés. 

* **anomaly_score**: Le score par défaut prévu dans [``config.py``](../../waad/utils/config.py) varie selon l'indicateur pour lequel une anomalie est remontée.
    - nb_authentications &rightarrow; 0.05
    - nb_computers_reached &rightarrow; 0.1
    - nb_new_computers_reached &rightarrow; 0.3
    - nb_privileges_granted &rightarrow; 0.2
* **reason**: Dépend également de l'indicateur en question.
    - nb_authentications &rightarrow; Abnormal behavior of asset on indicator
    - nb_computers_reached &rightarrow; IDEM
    - nb_new_computers_reached &rightarrow; IDEM
    - nb_privileges_granted &rightarrow; Abnormal behavior of asset with suspect outbreak of privileges
    
* **assets_concerned**: L'asset concerné
* **content**: Un objet ``TimeSeries`` qui lui-même hérite de ``StatSeries`` au format suivant : 

```
TimeSeries(StatSeries)
    time_step: int (seconds)
    start_time: str
    intermediary_content: Any
```

```
StatSeries
    name: str
    series: List[float]
    anomalies: List[int]
```

Ces objets implémentent la méthode display() qui affiche la série avec ses éventuelles anomalies. Dans le cas où l'indicateur utilise des contenus intermédiaires comme la liste des hôtes atteints par pas de temps, ces éléments sont stockés dans ``intermediary_content``.


### ComputeFaitNotablesFromIsolatedMachine
Lors d'un clustering sur des nomenclatures d'assets du parc informatique, on souhaite parfois relever ceux qui sont isolés par rapport aux autres. Cette classe permet cela. On lui donne en input une liste de strings que l'on sait isolée (par exemple le cluster ``None`` issue d'un clustering de la librairie).

* **anomaly_score**: Le score par défaut prévu dans [``config.py``](../../waad/utils/config.py) est de 0.3
* **reason**: Isolated asset after clustering
* **assets_concerned**: Chaque asset isolé
* **content**: ``None``


### ComputeFaitNotablesFromWINMachine
Lors du clustering sur des nomenclatures des machines du parc informatique, certaines portent des noms par défaut attribués aux machines Windows, elles sont davantages suspectes car les attaquants ne prennent pas forcément le temps de renommer les machines utilisées. Cette classe permet d'attribuer un score à ces machines.

* **anomaly_score**: Le score par défaut prévu dans [``config.py``](../../waad/utils/config.py) est de 0.3
* **reason**: WIN* default machine name
* **assets_concerned**: Chaque machine isolée commençant par WIN*
* **content**: ``None``


### ComputeFaitNotablesFromDESKTOPMachine
De la même manière que pour WIN*, les machines commençant par DESKTOP* portent des noms attribués par défaut et sont suspectes...

* **anomaly_score**: Le score par défaut prévu dans [``config.py``](../../waad/utils/config.py) est de 0.1
* **reason**: DESKTOP* default machine name
* **assets_concerned**: Chaque machine isolée commençant par DESKTOP*
* **content**: ``None``


## AnomalousAsset

Document d'explications concernant la classe [``AnomalousAsset``](../waad/utils/anomalous_asset.py) et la gestion des scores associés.

### La classe AnomalousAsset

```
AnomalousAsset
    asset: Asset
    anomaly_score: float
    faits_notables: List[FaitNotable]
```

* **asset**: L'asset (IP, machine ou compte) qui est considéré.
* **anomaly_score**: Score d'anormalité associé à l'asset, somme de tous les scores qui lui sont imputés par les faits notables associés.
* **faits_notables**: Ensemble des faits notables "reprochés" à l'asset.


### ComputeAnomalousAssets

```
ComputeAnomalousAssets
    faits_notables: List[FaitNotable]
    anomalous_assets: List[AnomalousAsset]
```

Cette classe, à travers sa méthode *run()* va permettre de croiser les faits notables issus de plusieurs sources et méthodes de détection d'anomalies. Les faits notables sont groupés par asset afin de construire des AnomalousAsset qui comportent un score d'anormalité et chaque fait notable qui lui est imputé comme explication.
