"""This module implements a class to identify bests combinations of grouped fields on a `Dataframe`."""


from collections import OrderedDict
import pandas as pd
from typing import List, Optional, Sequence, Tuple, Union


from waad.utils.constants import TupleAnalysisFields
from waad.utils.combinations_utils import custom_combinations_generator, flatten
from waad.utils.data import Data
from waad.utils.single_tuple_analyser import SingleTupleAnalyser


class AnalystTuplesAnalyser:
    """This class implements an analyst approach on rare tuples search.

    Attributes:
        data (pd.DataFrame): Set of authentication logs.
        exploratory_fields (List[Sequence[str]]): Fields or meta-fields of data to combine into tuples for analysis.
        max_aridity_per_field (int): Maximum aridity per field from `exploratory_fields` to consider in the algorithm.
        max_max_fragmentation_score (bool): If ``True``, then the fragmentation score is computed from the maximum of maximum of all non-monovaluted fields
            else, it is the average among all non-monovaluted fields.
        candidate (SingleTupleAnalyser): Best candidate tuple.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        exploratory_fields: List[Sequence[str]] = TupleAnalysisFields.FIRST_FIELDS_OF_INTERESTS.value,
        max_aridity_per_field: int = 5,
        max_max_fragmentation_score: bool = True,
    ):

        self.data = data
        self.exploratory_fields = exploratory_fields
        self.max_aridity_per_field = max_aridity_per_field
        self.max_max_fragmentation_score = max_max_fragmentation_score

        self.candidate = None

    def run(self):
        card = AnalystTuplesAnalyser.get_values_cardinality_from_fields(self.data, self.exploratory_fields)
        card = {key: value for key, value in sorted(card.items(), key=lambda item: len(item[1]), reverse=True) if 1 < len(value) <= self.max_aridity_per_field}

        remaining_fields = [field for field in card]

        if len(remaining_fields) > 0:
            scores = {}
            for field in card:
                always_monovalute_fields = {f: True for f in remaining_fields}
                linchpin_card_fields = {f: [] for f in remaining_fields}

                for combination in card[field]:
                    dataframe = Data.filter_dataframe_fields_on_values(self.data, filter_values={field: [combination]})
                    temp_card = AnalystTuplesAnalyser.get_values_cardinality_from_fields(dataframe, remaining_fields)
                    for f in temp_card:
                        linchpin_card_fields[f].append(len(temp_card[f]))
                    always_monovalute_fields = {f: always_monovalute_fields[f] and len(temp_card[f]) == 1 for f in always_monovalute_fields}
                candidate_tuple = [f for f, v in linchpin_card_fields.items() if all([element == 1 for element in v])]

                non_monovaluted_fields_fragmentation = [e for element in linchpin_card_fields.values() for e in element if not all([e == 1 for e in element])]
                if non_monovaluted_fields_fragmentation != []:
                    fragmentation_score = (
                        max(non_monovaluted_fields_fragmentation) if self.max_max_fragmentation_score else sum(non_monovaluted_fields_fragmentation) / len(non_monovaluted_fields_fragmentation)
                    )
                else:
                    fragmentation_score = 0

                scores[field] = {"score": len(candidate_tuple), "fragmentation_score": fragmentation_score, "candidate_tuple": candidate_tuple}

            if len(scores) >= 1:
                # The best candidate is the one that maximize the score
                maximum = max([scores[k]["score"] for k in scores])
                all_maxima = [k for k in scores if scores[k]["score"] == maximum]

                # And if again, several candidates are possible, we take the one that minimize fragmentation on non-monovaluted fields
                self.candidate = SingleTupleAnalyser(self.data, scores[min({k: scores[k] for k in all_maxima}, key=lambda k: scores[k]["fragmentation_score"])]["candidate_tuple"])
                self.candidate.run()

    @staticmethod
    def get_values_cardinality_from_field(data: pd.DataFrame, field: Union[List, str, Tuple]):
        # Filtering on v > 0 is due to categorical data in pandas, because it tends to display all categories even if they are equal to 0.
        return {k: v for k, v in data[field].value_counts().to_dict().items() if v > 0}

    @staticmethod
    def get_values_cardinality_from_fields(data, fields: List[Union[List, str, Tuple]]):
        return {field: AnalystTuplesAnalyser.get_values_cardinality_from_field(data, field) for field in fields}
