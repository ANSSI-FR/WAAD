# WAAD : Windows Authentication Anomaly Detection

Détection d'anomalie à partir des journaux d'authentification Windows 

Dans le cadre d'un projet en partenariat entre l'ANSSI et l'Etalab de la DINUM, WAAD a été conçu par la société `SIA Partners`.

:warning: Cet outil est une preuve de concept et ne doit pas être utilisé en production. 

## Installer le repo
### Cloner le repo
```shellS
$ git clone https://github.com/ANSSI-FR/WAAD
```

## Environnement de travail

### Dépendences
- Python 3.8 ou 3.7 au choix (voir pyproject.toml).
- `pip`
- `poetry`
- `python3.8-dev` ou `python3.7-dev`
- `libxml2-dev`
- `libxslt-dev`

### Dépendences
See [`pyproject.toml`](pyproject.toml).

### Installation et utilisation
Une fois que le repo est cloné, naviguez jusqu'à sa racine et créez l'environnement virtuel.

```console
$ cd waad
$ poetry install
```

Attendre que toutes les dépendances soient installées et entrer dans l'environnement.

```console
$ poetry shell
```

### Documentation Sphinx
Sous environnement `poetry`, une documentation automatique `Sphinx` peut-être générée sous forme de site hmtl.

```console
$ cd doc/
$ make html
```
Une fois construit, ouvrez le fichier `index.html` dans un navigateur:
```
doc
└───build
    └───html
        │   index.html
```

## Structure du projet
- **`ad-tree/`**: Package implémentant une structure ADTree pour calculer efficacement des nombres d'occurences.
- **`doc/`**: Documentation Sphinx générée automatiquement.
- **`notebooks/`**: Outils de prototypage pour les développeurs.
- **`waad/`**: Module Python.
