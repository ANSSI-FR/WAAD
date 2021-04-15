# Time Series - Pipeline de test 

## 0. Connexion à la base de données
Rentrer les coordonnées et les identifiants postrgreSQL de la table à utiliser.

</br>

## 1. Calcul des indicateurs selon les règles définies

### 1.1 Définition des règles permettant de compter les bons éléments dans les indicateurs

Les règles sont des objects de la librairie qui définissent des relations entre 2 assets sous certaines conditions. Pour chaque ligne d'authentifications de l'asset source, on vérifie si la règle est appliquée. Elle l'est si l'une des `conditions` au moins est appliquée (`ou` logique). Les conditions sont définies sous la forme de dictionnaires avec une structure de ce type :

```
{
    'pre_filters' : {'field_i': <possible values>, 'field_j': <possible values>},
    'filter_function': <function(row) -> bool>,
    'asset_1': <function(row) -> Asset>,
    'asset_2': <function(row) -> Asset>,
}
```

</br>

### 1.2 Calcul des indicateurs à partir de la ``Rule``

`pre_filters` donne des conditions à insérer dans la requête custom sur la base de données (afin de réduire le périmètre des données collectées et accélérer le process).

La requête arrive par morceaux pour ne pas surcharger la RAM et `filter_function` est une fonction appliquée à chaque ligne pour savoir si les assets doivent être construits. `filter_function` prend en argument une ligne du dataset (row) et à l'intérieur, on peut enchainer des formules logiques (ou même combiner plusieurs fonctions) pour renvoyer un booléen.

Si ce dernier est `True` alors les assets sont construits selon les fonctions de `asset_1` et `asset_2`. L'étape suivante est de rassembler une trace de cette ligne dans un cache, défini dans le block `ComputeIndicators`. Pour chaque asset_1, on garde le timestamps et l'asset_2 associée à chaque ligne que l'on a reconnu valide. Le cache a la structure suivante :

```
{
    asset_1_i: [{'systemtime': timestamp_k, 'asset_2': asset_2_k}, {'systemtime': timestamp_l, 'asset_2': asset_2_l}...]
    ... 
}
```

Une fois ce cache construit, on peut calculer les indicateurs habituels `nb_authentications` (toutes celles qui concernent asset_1 et respectent les règles), `nb_assets_reached` (pour chaque asset_1 nombre d'asset_2 atteints par pas de temps au sens de la règle ci-dessus), `nb_new_assets_reached` (pour chaque asset_1 nombre de nouveaux asset_2 atteints par pas de temps au sens de la règle ci-dessus).

`nb_new_assets_reached` se base sur un modèle légitime qui correspond à 25% de la durée d'activité de l'asset (paramétrable dans `config.py`)

</br>

### 1.3 Calcul des FaitsNotables associés
Application de l'IQR custom pour détecter des pics anormax dans les indicateurs et construction de FaitNotables. Pour rappel, un paramétrage est disponible dans `config.py`.

</br>

## 2. Calcul des AnomalousAssets
Regroupement des faits notables remontés sous des AnomalousAsset afin de faire ressortir ceux pour lesquels, le plus d'alertes sont remontées.
</br>
