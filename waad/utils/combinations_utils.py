"""This module implements some combinatorics related functions."""


from collections import Iterable
from itertools import combinations
from typing import List, Tuple, Union


def flatten(lst: Union[List, Tuple]) -> List:
    """Recursive function that flatten a list (of potential `Iterable` objects)."""
    if isinstance(lst, Iterable) and not isinstance(lst, (str, bytes)):
        return [a for i in lst for a in flatten(i)]
    else:
        return [lst]


def custom_combinations_generator(lst: List, length: int, excluded: List = []):
    """Generates combinations of elements from `lst` of size `length` without those containing subsequences in `excluded`."""
    return [
        comb
        for comb in combinations(lst, length)
        if not any(
            set(e).issubset(flatten(comb))
            if (isinstance(e, Iterable) and not isinstance(e, (str, bytes)))
            else set([e]).issubset(flatten(comb))
            for e in excluded
        )
    ]


def custom_combinations_generator_up_to(lst: List, length: int, excluded: List = []):
    """Generates combinations of elements from `lst` up to size `length` without those containing subsequences in `excluded`."""
    return [
        comb
        for size in range(1, length + 1)
        for comb in combinations(lst, size)
        if not any(
            set(e).issubset(flatten(comb))
            if (isinstance(e, Iterable) and not isinstance(e, (str, bytes)))
            else set([e]).issubset(flatten(comb))
            for e in excluded
        )
    ]


def get_all_pairs_of_subsets_indices(original_list: List):
    """Based on a binary approach to get all pairs of subset indices that constitute `original_list`."""
    res = []
    n = len(original_list)
    for i in range(2 ** (n - 1)):
        binary = [int(x) for x in format(i, f"0{n-1}b")]
        first_part = set([0] + [index + 1 for index, value in enumerate(binary) if value == 0])
        second_part = set([index + 1 for index, value in enumerate(binary) if value == 1])
        if len(first_part) > 0 and len(second_part) > 0:
            res.append([first_part, second_part])
    return res


def get_all_pairs_of_subsets(original_list: List):
    """Based on a binary approach to get all pairs of subsets that constitute `original_list`."""
    temp = get_all_pairs_of_subsets_indices(original_list)
    return [[[original_list[i] for i in indices_pair[0]], [original_list[i] for i in indices_pair[1]]] for indices_pair in temp]
