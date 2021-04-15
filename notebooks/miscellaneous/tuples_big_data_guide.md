# Tuples "Big data" - Pipeline de test 

## Installation du package adtree-py
* Ouvrez le notebook de prototype ``prototype_tuples_big_data.ipynb``
```
waad
└───notebooks/
    └───miscellaneous/
        │   prototype_tuples_big_data.ipynb
```

## Load data
### Exemple of request
Dans ce bloc, il convient de requêter le dataset de la manière souhaitée. La requête proposée permet de charger les 2 500 000 premières authentifications du jeu qui sont des 4624.

</br>

### Filtering block
Possibilité de filtrer la requête obtenue sur un ou plusieurs champs avec les fonctions génériques de la librairie. 

</br>

### Pre-processing
* Récupération des méta-champs définis par le métier
* Construction des méta-champs dans le tableau d'authentifications requêté
* Conversion des méta-champs en format catégoriel et récupération d'une table de conversion catégorie-modalité sous la forme d'un dictionnaire
* Récupération de la ``records_table`` au format catégoriel
* Récupération de la ``arity_list``

</br>

## ADTree pipeline

</br>

### Building ADTree
Construction de l'arbre à partir de ``records_table`` et ``arity_list``. Les 2 implémentations privilégiées sont ``SparseADTree`` et ``LeafSparseADTree`` qui permettent de ne pas poursuivre la construction ultérieure des noeuds de cardinal nul. Ceci permet de gagner du temps et d'économiser de la place en RAM. L'implémentation ``LeafSparseADTree`` est encore plus avancée car elle permet de stocker directement des pointeurs vers les authentifications de ``records_table`` dans les derniers noeuds (les feuilles) de l'arbre, ce qui permet d'économiser encore plus de place en RAM.

</br>

### Building cache
Comme il est impossible de parcourir les tables de contingence issues de l'arbre autrement que par des requêtes, nous construisons un cache contenant toutes les occurrences des combinaisons utiles (ie de nombre d'occurrences > 0). Pour cela, nous raisonnons par 'couche', en requêtant d'abord toutes les modalités des méta-champs (niveau 1), puis à partir de cela les doublets (niveau 2) et à partir des doublets d'occurrences non nuls, les triplets (niveau 3) et ainsi de suite jusqu'au niveau demandé en paramètre. Cela permet de conserver toutes les occurrences utiles dans un dictionnaire dans lequel on peut naviguer facilement contrairement à l'arbre.

</br>

### Compute mutual information
L'information mutuelle doit être calculée entre toutes les paires de sous-ensembles de méta-champs pour le niveau du cache auquel on travaille. Si l'on se place au niveau 3, et que l'on a 3 méta-champs A, B, C, on doit calculer l'information mutuelle pour ({A, B}, C) et ({A, C}, B) et ({B, C}, A)... Toutes les informations mutuelles d'un même niveau peuvent ensuite être affichées sur un graphe afin de donner la possibilité à l'investigateur de choisir la valeur du seuil 'mu'. Par défaut, 'mu' est fixé à 0.1, suite aux investigations menées sur le dataset anonymisé. 

</br>

### Scores computation 
Calcule les scores de toutes les paires de sous-ensembles des méta-champs pour le niveau étudié, si le nombre d'occurrences des 2 éléments de la paire est supérieur au support ``t_alpha``.

</br>

### Scores visualization 
Affiche les 20 éléments de score le plus faible, qui sont les plus suspects. Le nombre d'éléments visualisable est paramétrable.
