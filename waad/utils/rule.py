"""This module implements the `Rule` object."""


from enum import auto, Enum
from typing import Any, Callable, Dict, List, Optional


class Link(Enum):
    """Defines a link between 2 assets."""

    CONNECTE_VERS = auto()
    SE_CONNECTE_SUR = auto()


class Probability(Enum):
    """Defines the certainty of a link between 2 assets."""

    CERTAIN = auto()
    PROBABLE = auto()


class Relation:
    """Gathers a link between 2 assets and its certainty.

    Attributes:
        link (Link): Link we want to define for the relation.
        probability (Probability): Corresponding certainty of the link.
    """

    def __init__(self, link: Link, probability: Probability):
        self.link = link
        self.probability = probability


class Rule:
    """Defines a `Relation` between 2 assets and the conditions for which it applies.

    Attributes:
        relation (Relation): Relation between the 2 types of assets.
        conditions (List[Dict]): Different conditions under which the `relation` is defined. The structure of a condition is the following :

    .. code-block:: python

        {
            'pre_filters' : {'field_i': <possible values>, 'field_j': <possible values>},
            'asset_1': <function(row) -> Asset>,
            'asset_2': <function(row) -> Asset>,
            'filter_function': <function(row) -> bool>,
        }

    """

    def __init__(self, relation: Relation, conditions: List[Dict]):
        self.relation = relation
        self.conditions = conditions
