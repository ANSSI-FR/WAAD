"""This module implements a `Dataframe` grouping class on columns."""


from datetime import datetime
from IPython.display import display
import pandas as pd
from typing import Dict, List, Union, Tuple


from waad.utils.constants import Fields


class SingleTupleAnalyser:
    """This class defines a `SingleTupleAnalyser` pipeline.

    Attributes:
        data (pd.DataFrame): Set of authentication logs.
        fields (List[Union[str, Iterable]]): Fields of data to combine into tuples for analysis.
    """

    def __init__(self, data: pd.DataFrame, fields: List[str]):
        self.data = data
        self.fields = fields

        self.groups: Dict

    def run(self):
        """Runs the pipeline."""
        self.groups = {k: v for k, v in self.data.groupby(by=[f for f in self.fields]).groups.items() if len(v) > 0}

    def get_summary(self):
        """Get a summary of the corresponding grouping as a `pd.Dataframe` with duration added as an indication."""
        try:
            summary = []
            for k, v in self.groups.items():
                times = [datetime.fromisoformat(str(x).replace("Z", "+00:00")) for x in self.data.loc[v]["systemtime"]]
                max_time = max(times)
                min_time = min(times)
                field = k
                if len(self.fields) == 1:
                    field = [field]
                summary.append(list(field) + [len(v), max_time - min_time])
            multi_index = SingleTupleAnalyser.get_multi_index_from_fields(self.fields).append(
                pd.MultiIndex.from_arrays([["data", "data"], ["cardinality", "duration"]])
            )
            return pd.DataFrame(summary, columns=multi_index)
        except KeyError:
            return pd.DataFrame()

    def display_centered_summary(self):
        display(
            self.get_summary().style.set_table_styles(
                [{"selector": "th", "props": [("text-align", "center")]}, {"selector": "td", "props": [("text-align", "center")]}]
            )
        )

    def get_given_tuple_slice(self, given_tuple: Tuple[Union[str, int], ...]) -> pd.DataFrame:
        """Returns a slice of `data`, corresponding to `given_tuple`."""
        return self.data.iloc[self.groups[given_tuple]]

    @staticmethod
    def get_multi_index_from_fields(fields: List[Union[Tuple[str, ...], List[str], str]]):
        columns: List[List] = [[], []]
        for field in fields:
            if isinstance(field, tuple) or isinstance(field, list):
                meta_field = Fields.get_meta_field_from_tuple(tuple(field))
                columns[0].append(meta_field.name)
                columns[1].append(field)
            else:
                columns[0].append(field)
                columns[1].append(field)

        return pd.MultiIndex.from_arrays(columns, names=("meta_fields", "flatten_fields"))
