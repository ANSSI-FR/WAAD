"""This module implements some Tuples Big Data related classes and functions.

It comes from the implementation of a scientific paper: Detecting Anomalous Records in Categorical Datasets - Kaustav Das & Jeff Schneider (Carnegie Mellon University)
"""


from collections import Iterable
from IPython.display import display
import json
import math
import matplotlib.pyplot as plt
import numpy as np
import numpy.matlib
import pandas as pd
from scipy.signal import find_peaks
import sys
from tqdm import tqdm
from typing import Any, Dict, List, Optional, Tuple, Union


from ad_tree.sparse_ADTree import ADNode
from ad_tree.iterated_tree_contingency_table import ContingencyTable


from waad.utils.data import Data
from waad.utils.combinations_utils import custom_combinations_generator, get_all_pairs_of_subsets_indices


class Cache:
    """This class implements a storage structure for all contingency tables.

    Attributes:
        adtree (ADNode): ADTree we want to work on.
        meta_fields (List): The list of meta fields of the dataset.
        maximum_layer (int): The target maximum layer we want to reach.
        cache (Dict[int, Dict[Tuple, Dict[Tuple, int]]]): The actual structure, layered by level (size of combinations) and meta-
            fields combinations. For instance level 2 contains all size 2 combinations of meta-fields and their modalities.
    """

    def __init__(self, adtree: ADNode, meta_fields: List, maximum_layer: int):
        self.adtree = adtree
        self.meta_fields = meta_fields
        self.maximum_layer = maximum_layer
        self.cache: Dict[int, Dict[Tuple, Dict[Tuple, int]]]

    def initialize_cache(self):
        self.cache = {1: {}}
        for i in tqdm(range(len(self.meta_fields)), file=sys.stdout):
            contab = ContingencyTable([i + 1], self.adtree)
            self.cache[1][tuple([i])] = contab.get_table()

    def add_new_cache_layer(self):
        m = max(self.cache.keys())
        self.cache[m + 1] = {}
        for new_combination in tqdm(custom_combinations_generator(list(range(len(self.meta_fields))), length=m + 1), file=sys.stdout):
            contab = ContingencyTable([e + 1 for e in new_combination], self.adtree)
            self.cache[m + 1][new_combination] = contab.get_table()

    def run(self):
        print("Initialize cache")
        self.initialize_cache()

        for k in range(2, self.maximum_layer + 1):
            print(f"Build cache layer {k}")
            self.add_new_cache_layer()


class MetaField:
    """This class implements a facilitator for meta-field handling. It eases conversion between standard data to categorical.

    Attributes:
        fields (Union[Tuple[str, ...], str, int]): The actual designation of the meta-field, either as a column name, a tuple of columns 
            name or as an int encoding the categorical value of the meta-field.
        name (Optional[str]): Potential 'summary' name of the meta-field.
        converter (Optional[Dict[Tuple[str, ...], Dict]]): Dict containing the conversion material from str to code.

    """

    def __init__(self, fields: Union[Tuple[str, ...], str, int], name: Optional[str] = None, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        self.fields = fields
        self.name = name
        self.converter = converter

    def __eq__(self, obj: Any):
        return isinstance(obj, MetaField) and obj.name == self.name and obj.fields == self.fields

    def __hash__(self):
        return hash((self.fields, self.name))

    def __repr__(self):
        return str(self.fields)

    def to_index(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            converter = converter if converter is not None else self.converter
            self.fields = list(converter.keys()).index(self.fields)
        except Exception:
            pass

    def get_to_index(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            converter = converter if converter is not None else self.converter
            return MetaField(fields=list(converter.keys()).index(self.fields), name=self.name, converter=converter)
        except Exception:
            return None

    def to_categories(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            converter = converter if converter is not None else self.converter
            self.fields = list(converter.keys())[self.fields]
        except Exception:
            pass

    def get_to_categories(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            converter = converter if converter is not None else self.converter
            return MetaField(fields=list(converter.keys())[self.fields], name=self.name, converter=converter)
        except Exception:
            return None


class Modality:
    """This class implements a facilitator for modality handling. It eases conversion between standard data to categorical.

    Attributes:
        meta_field (MetaField): The `MetaField` object behind the modality.
        modality (Union[Tuple[str, ...], str, int]): The actual designation of the modality, either as a column name, a tuple of columns 
            name or as an int encoding the categorical value of the modality.
        converter (Optional[Dict[Tuple[str, ...], Dict]]): Dict containing the conversion material from str to code. See above description.
    """

    def __init__(self, meta_field: MetaField, modality: Tuple[str, ...], converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        self.meta_field = meta_field
        self.modality = modality
        self.converter = converter

    def __eq__(self, obj: Any):
        return isinstance(obj, Modality) and obj.meta_field == self.meta_field and obj.modality == self.modality

    def __hash__(self):
        return hash((self.meta_field, self.modality))

    def __repr__(self):
        return "[" + repr(self.meta_field) + "]" + " - " + str(self.modality)

    def to_code(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            converter = converter if converter is not None else self.converter
            self.modality = list(converter[self.meta_field.fields].keys())[list(converter[self.meta_field.fields].values()).index(self.modality)]
            self.meta_field.to_index(converter)
        except Exception:
            pass

    def get_to_code(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            converter = converter if converter is not None else self.converter
            return Modality(
                meta_field=self.meta_field.get_to_index(converter),
                modality=list(converter[self.meta_field.fields].keys())[list(converter[self.meta_field.fields].values()).index(self.modality)],
                converter=converter,
            )
        except Exception:
            return None

    def to_categories(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            converter = converter if converter is not None else self.converter
            self.meta_field.to_categories(converter)
            self.modality = converter[self.meta_field.fields][self.modality]
        except Exception:
            pass

    def get_to_categories(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            converter = converter if converter is not None else self.converter
            meta_field = self.meta_field.get_to_categories(converter)
            return Modality(meta_field=meta_field, modality=converter[meta_field.fields][self.modality], converter=converter)
        except Exception:
            return None

    @staticmethod
    def convert_meta_field_code_to_modality(meta_field: MetaField, code: int, converter: Dict[Tuple[str, ...], Dict]):
        return Modality(meta_field, converter[meta_field][code])


class Score:
    """This class implements a `Score` object between 2 combinations of modalities.

    Attributes:
        A_a (Tuple[Modality, ...]): Tuple of `Modality` objects.
        B_b (Tuple[Modality, ...]): Tuple of `Modality` objects.
        score (float): The actual score of the pairings `A_a` and `B_b`.
        cardinality (int): The cardinality of the joint modality defined by `A_a` and `B_b`.
        converter (Optional[Dict[Tuple[str, ...], Dict]]): Dict containing the conversion material from str to code. See above description.
    """

    def __init__(self, A_a: Tuple[Modality, ...], B_b: Tuple[Modality, ...], score: float, cardinality: int, converter: Optional[Dict] = None):
        self.A_a = A_a
        self.B_b = B_b
        self.score = score
        self.cardinality = cardinality
        self.converter = converter

    def __repr__(self):
        return f"""
            'A_a': {[repr(e) for e in self.A_a]},
            'B_b': {[repr(e) for e in self.B_b]},
            'score': {self.score},
            'cardinality': {self.cardinality}
        """

    def to_code(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        converter = converter if converter is not None else self.converter
        for modality in self.A_a + self.B_b:
            modality.to_code(converter)

    def get_to_code(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            return Score(A_a=tuple([m.get_to_code(converter) for m in self.A_a]), B_b=tuple([m.get_to_code(converter) for m in self.B_b]), score=self.score, cardinality=self.cardinality)
        except Exception:
            return self

    def to_categories(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        converter = converter if converter is not None else self.converter
        for modality in self.A_a + self.B_b:
            modality.to_categories(converter)

    def get_to_categories(self, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        try:
            return Score(A_a=tuple([m.get_to_categories(converter) for m in self.A_a]), B_b=tuple([m.get_to_categories(converter) for m in self.B_b]), score=self.score, cardinality=self.cardinality)
        except Exception:
            return self

    def is_in(self, other: Any):
        try:
            return set(self.A_a + self.B_b).issubset(set(other.A_a + other.B_b))
        except Exception:
            return False

    def to_dict(self):
        return {
            "attributes_pair": (tuple([m.meta_field.fields for m in self.A_a]), tuple([m.meta_field.fields for m in self.B_b])),
            "modalities": (tuple([m.modality for m in self.A_a]), tuple([m.modality for m in self.B_b])),
            "score": self.score,
            "cardinality": self.cardinality,
        }

    @staticmethod
    def from_dict(score: Dict, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        return Score(
            A_a=tuple([Modality(MetaField(fields=mf, converter=converter), m, converter) for mf, m in zip(score["attributes_pair"][0], score["modalities"][0])]),
            B_b=tuple([Modality(MetaField(fields=mf, converter=converter), m, converter) for mf, m in zip(score["attributes_pair"][1], score["modalities"][1])]),
            score=score["score"],
            cardinality=score["cardinality"],
        )


class ScoreGroup:
    """This class implements a group of scores gathered together for common reasons (ex: same modalities arranged differently...).

    Attributes:
        score_group (List[Score]): ADTree we want to work on.
        score (float): Score of the grouping (smaller rank among all scores).
        ranks (Optional[List[Tuple[int, int]]]): All ranks of the scores in their given level. The first int corresponds to the actual rank and the second
            to the number of scores computed on the level.
    """

    def __init__(self, score_group: List[Score], score: float, ranks: Optional[List[Tuple[int, int]]] = None):
        self.score_group = score_group
        self.score = score
        self.ranks = ranks

    def display(self):
        print(f"score : {self.score}")
        try:
            display(pd.DataFrame([dict(score.get_to_categories().to_dict(), **{"rank": f"{ranks[0]} / {ranks[1]}"}) for score, ranks in zip(self.score_group, self.ranks)]))
        except Exception:
            display(pd.DataFrame([dict(score.to_dict(), **{"rank": f"{ranks[0]} / {ranks[1]}"}) for score, ranks in zip(self.score_group, self.ranks)]))

    def to_dict(self):
        return {"score_group": [score.get_to_categories().to_dict() for score in self.score_group], "score": self.score, "ranks": self.ranks}

    @staticmethod
    def from_dict(score_group_dict: Dict):
        return ScoreGroup(score_group=[Score.from_dict(score) for score in score_group_dict["score_group"]], score=score_group_dict["score"], ranks=score_group_dict["ranks"])


class ComputeMutualInfoOnGivenLevel:
    """This class implements the computation of mutual information on a given level.

    Attributes:
        cache (Cache): The cache object we work on.
        level (int): The given level of the cache we want to compute mutual info on.
        mutual_info_scores (Dict[Tuple, float]): Mutual info scores computed on all combinations of meta-fields of size `level`.
    """

    def __init__(self, cache: Cache, level: int):
        self.cache = cache
        self.level = level
        self.mutual_info_scores: Dict[Tuple, float] = {}

    def run(self):
        for k in self.cache.cache[self.level].keys():
            for indices_pair in get_all_pairs_of_subsets_indices(k):
                start_meta_fields = tuple([k[i] for i in indices_pair[0]])
                end_meta_fields = tuple([k[i] for i in indices_pair[1]])

                self.mutual_info_scores[(start_meta_fields, end_meta_fields)] = 0

        N = self.cache.adtree.array_record.records_length
        for k in self.cache.cache[self.level].keys():
            for indices_pair in get_all_pairs_of_subsets_indices(k):
                start_meta_fields = tuple([k[i] for i in indices_pair[0]])
                end_meta_fields = tuple([k[i] for i in indices_pair[1]])

                for modalities, count in self.cache.cache[self.level][k].items():
                    start_modalities = tuple([modalities[i] for i in indices_pair[0]])
                    end_modalities = tuple([modalities[i] for i in indices_pair[1]])

                    count_start = self.cache.cache[len(start_meta_fields)][start_meta_fields][start_modalities]
                    count_end = self.cache.cache[len(end_meta_fields)][end_meta_fields][end_modalities]

                    self.mutual_info_scores[(start_meta_fields, end_meta_fields)] += (count / N) * math.log((N * count) / (count_start * count_end))

        self.mutual_info_scores = {k: v for k, v in sorted(self.mutual_info_scores.items(), key=lambda item: item[1])}

    def plot_mutual_info(self, index_elbow: Optional[int] = None):
        fig, ax = plt.subplots(figsize=(15, 10))
        curve = list(self.mutual_info_scores.values())
        ax.plot(curve)
        ax.set_title(f"Mutual info scores on level {self.level}")
        if index_elbow is not None:
            ax.vlines([index_elbow], ymin=min(curve), ymax=max(curve), colors="r")
        return fig

    def compute_index_elbow(self, prominence: float = 0.1, distance: Optional[float] = None):
        curve = list(self.mutual_info_scores.values())
        n_points = len(curve)
        all_coord = np.vstack((range(n_points), curve)).T

        line_vec = all_coord[-1] - all_coord[0]
        line_vec_norm = line_vec / np.sqrt(np.sum(line_vec ** 2))
        vec_from_first = all_coord - all_coord[0]
        scalar_product = np.sum(vec_from_first * np.matlib.repmat(line_vec_norm, n_points, 1), axis=1)
        vec_from_first_parallel = np.outer(scalar_product, line_vec_norm)
        vec_to_line = vec_from_first - vec_from_first_parallel
        dist_to_line = np.sqrt(np.sum(vec_to_line ** 2, axis=1))

        distance = distance if distance is not None else len(self.mutual_info_scores) // 5
        peaks, _ = find_peaks(dist_to_line, height=0, prominence=prominence, distance=distance)

        return peaks[0]

    def get_mu(self, index_elbow: int):
        return list(self.mutual_info_scores.values())[index_elbow]

    def get_pairings_to_keep(self, mu: float):
        return [k for k, v in self.mutual_info_scores.items() if v >= mu]

    def get_last_n_eliminated(self, mu: float, last_n: int, converter: Optional[Dict[Tuple[str, ...], Dict]]):
        return pd.DataFrame(
            sorted(
                {tuple([MetaField(fields=e, converter=converter).get_to_categories(converter).fields for ee in k for e in ee]): v for k, v in self.mutual_info_scores.items() if v < mu}.items(),
                key=lambda item: item[1],
            )[-last_n:],
            columns=["meta_fields_pair", "score"],
        )


class ComputeScoreOnGivenLevel:
    """This class implements the computation of scores on a given level.

    Attributes:
        cache (Cache): The cache object we work on.
        level (int): The given level of the cache we want to compute scores on.
        t_alpha (int): Minimum cardinality we want on a combination of modalities to compute the score.
        pairings_to_keep (List): All pairings of meta-fields we want to explore for score computation. 
    """

    def __init__(self, cache: Cache, level: int, t_alpha: int, pairings_to_keep: List = []):
        self.cache = cache
        self.level = level
        self.t_alpha = t_alpha
        self.pairings_to_keep = pairings_to_keep
        self.scores: List[Dict] = []

    def run(self):
        N = self.cache.adtree.array_record.records_length
        for k in self.cache.cache[self.level].keys():
            for indices_pair in get_all_pairs_of_subsets_indices(k):
                start_meta_fields = tuple([k[i] for i in indices_pair[0]])
                end_meta_fields = tuple([k[i] for i in indices_pair[1]])

                if (start_meta_fields, end_meta_fields) in self.pairings_to_keep:
                    for modalities, count in self.cache.cache[self.level][k].items():
                        start_modalities = tuple([modalities[i] for i in indices_pair[0]])
                        end_modalities = tuple([modalities[i] for i in indices_pair[1]])

                        count_start = self.cache.cache[len(start_meta_fields)][start_meta_fields][start_modalities]
                        count_end = self.cache.cache[len(end_meta_fields)][end_meta_fields][end_modalities]

                        if count_start >= self.t_alpha and count_end >= self.t_alpha:
                            self.scores.append(
                                {
                                    "attributes_pair": (start_meta_fields, end_meta_fields),
                                    "modalities": (start_modalities, end_modalities),
                                    "score": (count + 1) * (N + 2) / ((count_start + 1) * (count_end + 1)),
                                    "cardinality": count,
                                }
                            )
        self.scores.sort(key=lambda p: p["score"])

    def get_firsts_abnormal_pairings(self, firsts_n: int, converter: Optional[Dict[Tuple[str, ...], Dict]] = None, min_card: Optional[int] = None):
        if min_card is not None:
            index, count = 0, 0
            scores = []
            while count < firsts_n and index < len(self.scores):
                score = self.scores[index]
                if score["cardinality"] >= min_card:
                    scores.append(Score.from_dict(score, converter).get_to_categories().to_dict())
                    count += 1
                index += 1
            return pd.DataFrame(scores)
        return pd.DataFrame([Score.from_dict(score, converter).get_to_categories().to_dict() for score in self.scores[:firsts_n]])

    def save_firsts_abnormal_pairings(self, firsts_n: int, converter: Optional[Dict[Tuple[str, ...], Dict]] = None, min_card: Optional[int] = None, path: str = "./firsts_abnormal_pairings.csv"):
        res = self.get_firsts_abnormal_pairings(firsts_n, converter, min_card)
        res.to_csv(path)

    def get_most_frequent_pairings_categorical(self, A: Tuple[str, ...], a: Tuple[str, ...], B: Tuple[str, ...], firsts_n: int):
        def filter_function(x):
            try:
                index = list(x["attributes_pair"]).index(A)
                return True if (x["modalities"][index] == a and B in x["attributes_pair"]) else False
            except Exception:
                return False

        temp = list(filter(lambda x: filter_function(x), self.scores))[-firsts_n:]
        if temp == []:
            return []
        else:
            index = list(temp[0]["attributes_pair"]).index(B)
            return [{"attributes_pair": (A, B), "modalities": (a, score["modalities"][index]), "score": score["score"], "cardinality": score["cardinality"]} for score in temp]

    def get_most_frequents_pairings_understandable(self, A: Tuple[str, ...], a: Tuple[str, ...], B: Tuple[str, ...], firsts_n: int, converter: Dict[Tuple[str, ...], Dict]):
        return [Score.from_dict(score, converter).get_to_categories().to_dict() for score in self.get_most_frequent_pairings_categorical(A, a, B, firsts_n)]

    def get_splitted_score_on_modalities(self, score: Dict[str, Any]):
        try:
            return {
                "attributes_pair": score["attributes_pair"],
                "fixed_modality": score["modalities"][0],
                "varying_modality": score["modalities"][1],
                "score": score["score"],
                "cardinality": score["cardinality"],
            }
        except Exception:
            return {}

    def get_most_frequents_subpairings(self, converter: Dict[Tuple[str, ...], Dict], index_number: Optional[int] = None, score: Optional[Score] = None, firsts_n: int = 20):
        if index_number is not None:
            local_score = self.scores[index_number]
            score_obj = Score.from_dict(local_score).get_to_categories(converter)
        else:
            score_obj = score.get_to_categories(converter)
            local_score = score.to_dict()

        return [
            {
                "modalities": score_obj.A_a,
                "frequently_associated": [
                    self.get_splitted_score_on_modalities(score)
                    for score in self.get_most_frequents_pairings_understandable(
                        local_score["attributes_pair"][0], local_score["modalities"][0], local_score["attributes_pair"][1], firsts_n, converter
                    )
                ],
            },
            {
                "modalities": score_obj.B_b,
                "frequently_associated": [
                    self.get_splitted_score_on_modalities(score)
                    for score in self.get_most_frequents_pairings_understandable(
                        local_score["attributes_pair"][1], local_score["modalities"][1], local_score["attributes_pair"][0], firsts_n, converter
                    )
                ],
            },
        ]

    def display_most_frequents_subpairings(self, converter: Dict[Tuple[str, ...], Dict], index_number: Optional[int] = None, score: Optional[Score] = None, firsts_n: int = 20):
        res = self.get_most_frequents_subpairings(converter=converter, index_number=index_number, score=score, firsts_n=firsts_n)

        if index_number is not None:
            score_obj = Score.from_dict(self.scores[index_number])
        else:
            score_obj = score

        print("Score studied")
        display(pd.DataFrame([score_obj.get_to_categories(converter).to_dict()]))

        print()
        print("Frequently associated")
        display(pd.DataFrame(res[0]["frequently_associated"]))
        display(pd.DataFrame(res[1]["frequently_associated"]))

    def get_corresponding_authentications(self, data: pd.DataFrame, index_number: Optional[int] = None, score: Optional[Score] = None, converter: Optional[Dict] = None):
        if index_number is not None:
            score_dict = Score.from_dict(self.scores[index_number], converter).get_to_categories(converter).to_dict()
        else:
            score_dict = score.get_to_categories(converter).to_dict()

        filter_values = {meta_field: [modality] for meta_fields, modalities in zip(score_dict["attributes_pair"], score_dict["modalities"]) for meta_field, modality in zip(meta_fields, modalities)}
        return Data.filter_dataframe_fields_on_values(data, filter_values)


class ScoreGroupings:
    """This class implements the computation of `ScoreGroup` from different levels of pairings scores.

    Attributes:
        csogls (Dict[str, ComputeScoreOnGivenLevel]): Dict containing a `ComputeScoreOnGivenLevel` object per level.
        max_level (List): The max level to consider for scores.
        firsts_n (int): The n firsts scores to consider per level.
        converter (Optional[Dict[Tuple[str, ...], Dict]]): Dict containing the conversion material from str to code. See above description.
    """

    def __init__(self, csogls: Dict[str, ComputeScoreOnGivenLevel], max_level: int, firsts_n: int, converter: Dict[Tuple[str, ...], Dict]):
        self.csogls = csogls
        self.max_level = max_level
        self.firsts_n = firsts_n
        self.converter = converter

        self.score_groupings: List[ScoreGroup] = []

    def run(self):
        all_scores = {}
        for level, csogl in self.csogls.items():
            all_scores[level] = [(rank, Score.from_dict(score, self.converter)) for rank, score in enumerate(csogl.scores[: self.firsts_n])]

        for level in range(2, self.max_level + 1):
            already_used = []
            for score_rank, score in all_scores[level]:
                if score not in already_used:
                    already_used.append(score)
                    new_grouping = [(score, score_rank)]
                    for rank, other_score in [(r, s) for r, s in all_scores[level] if s != score]:
                        if score.is_in(other_score):
                            new_grouping.append((other_score, rank))
                            already_used.append(other_score)

                    for rank, other_score, lvl in [(rank, s, lvl) for lvl, ss in all_scores.items() if lvl > level for rank, s in ss]:
                        if score.is_in(other_score):
                            new_grouping.append((other_score, rank))
                            all_scores[lvl].remove((rank, other_score))

                    self.score_groupings.append(
                        ScoreGroup(score_group=[s for s, _ in new_grouping], score=min([rank for _, rank in new_grouping]), ranks=[(rank, self.firsts_n) for _, rank in new_grouping])
                    )

        self.score_groupings.sort(key=lambda sg: sg.score)


class ComputeMutualInfoScoreGroupings:
    """This class implements the whole pipeline of tuples big data from a `Cache` object: computation of all mutual info scores, then computation of scores
    and finally gouping of them.

    Attributes:
        max_level (int): The max level we consider.
        cache (Cache): The cache object we work on.
        mu (float): The cutting threshold on mutual info scores. Under mu, a combination of meta-fields is considered too poorly correlated.
        t_alpha (int): Minimum cardinality we want on a combination of modalities to compute the score.
        firsts_n (int): The n firsts scores to consider per level.
        converter (Optional[Dict[Tuple[str, ...], Dict]]): Dict containing the conversion material from str to code. See above description.
    """

    def __init__(self, max_level: int, cache: Cache, mu: float, t_alpha: int, firsts_n: int, converter: Optional[Dict[Tuple[str, ...], Dict]]):
        self.max_level = max_level
        self.cache = cache
        self.mu = mu
        self.t_alpha = t_alpha
        self.firsts_n = firsts_n
        self.converter = converter

        self.cmiogls: Dict[int, ComputeMutualInfoOnGivenLevel] = {}
        self.csogls: Dict[int, ComputeScoreOnGivenLevel] = {}

        self.sg: ScoreGroupings

    def run(self):
        for level in range(2, self.max_level + 1):
            cmiogl = ComputeMutualInfoOnGivenLevel(self.cache, level)
            cmiogl.run()
            pairings_to_keep = cmiogl.get_pairings_to_keep(self.mu)
            self.cmiogls[level] = cmiogl

            csogl = ComputeScoreOnGivenLevel(self.cache, level, self.t_alpha, pairings_to_keep)
            csogl.run()
            self.csogls[level] = csogl

        self.sg = ScoreGroupings(self.csogls, max_level=self.max_level, firsts_n=self.firsts_n, converter=self.converter)
        self.sg.run()

    def display_most_frequents_subpairings(self, score: Score, converter: Dict[Tuple[str, ...], Dict], firsts_n: int = 10):
        level = len(score.A_a) + len(score.B_b)
        self.csogls[level].display_most_frequents_subpairings(score=score, firsts_n=firsts_n, converter=converter)

    def get_corresponding_authentications(self, data: pd.DataFrame, score: Optional[Score] = None, converter: Optional[Dict[Tuple[str, ...], Dict]] = None):
        level = len(score.A_a) + len(score.B_b)
        return self.csogls[level].get_corresponding_authentications(data=data, score=score, converter=converter)

    @staticmethod
    def save_static(
        path: str,
        table_name: str,
        psql_request: str,
        meta_fields: List[Union[str, Tuple[str, ...]]],
        t_alpha: float,
        mus: List[float],
        firsts_n: int,
        csogls: Dict[int, ComputeScoreOnGivenLevel],
        score_groups: ScoreGroupings,
        converter: Dict,
    ):

        export_dict = {"table_name": table_name, "psql_request": psql_request, "meta_fields": meta_fields, "t_alpha": t_alpha, "firsts_n": firsts_n, "mus": mus}
        for level, csogl in csogls.items():
            export_dict[f"scores_level_{level}"] = [Score.from_dict(score).get_to_categories(converter).to_dict() for score in csogl.scores[:firsts_n]]

        export_dict["score_groupings"] = [score_group.to_dict() for score_group in score_groups.score_groupings]

        with open(path, "w") as outfile:
            json.dump(export_dict, outfile)

    def save(self, path: str, table_name: str, psql_request: str, meta_fields: List[Union[str, Tuple[str, ...]]]):
        ComputeMutualInfoScoreGroupings.save_static(
            path=path,
            table_name=table_name,
            psql_request=psql_request,
            meta_fields=meta_fields,
            t_alpha=self.t_alpha,
            mus=[self.mu for _ in range(2, self.max_level + 1)],
            firsts_n=self.firsts_n,
            csogls=self.csogls,
            score_groups=self.sg,
            converter=self.converter,
        )

    @staticmethod
    def display_from_json(json_file: str):
        with open(json_file) as file:
            data = json.load(file)
            print(f"table_name: {data['table_name']}")
            print()
            print(f"psql_request: {data['psql_request']}")
            print()
            print(f"meta_fields: {data['meta_fields']}")
            print()
            print(f"t_alpha: {data['t_alpha']}")
            print()
            print(f"mus: {data['mus']}")
            print()

            for k, v in data.items():
                if k.startswith("scores_level_"):
                    print(k)
                    display(pd.DataFrame(data[k]))

            print()
            for index, score_group in enumerate(data["score_groupings"]):
                print(f"ScoreGroup index : {index}")
                ScoreGroup.from_dict(score_group).display()
