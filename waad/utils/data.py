"""This module implements some facilities related to data handling."""


from collections import Iterable
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union


class Data:
    """This class implements a DataFrame wrapper containing facilities. It is mostly a tool box full of static methods.

    Attributes:
        dataframe (pd.DataFrame): List of strings to cluster.
        converter (Optional[Dict[Tuple[str, ...], Dict]]): Dict containing the conversion material from str to code. See description in tuples_big_data.py.
    """

    def __init__(self, dataframe: pd.DataFrame, converter: Optional[Dict] = None):
        self.dataframe = dataframe
        self.converter = converter

    @staticmethod
    def build_meta_fields(data: pd.DataFrame, meta_fields: List, inplace: bool = True):
        """Build meta-fields on the dataset and remove the single columns that are in `meta_fields` to preserve RAM."""
        if inplace:
            temp = data
        else:
            temp = data.copy(deep=True)

        for meta_field in meta_fields:
            if isinstance(meta_field, Iterable) and not isinstance(meta_field, (str, bytes)):
                temp[meta_field] = list(zip(*[data[f] for f in meta_field]))
                temp.drop(columns=list(meta_field), inplace=True)

        if not inplace:
            return temp

    @staticmethod
    def set_as_categorical(data: pd.DataFrame, fields_to_categorize: List[Union[str, Tuple[str, ...]]], inplace: bool = True, additional_info: Dict = {}):
        """Convert a dataframe to categorical data and return the corresponding converter dictionary."""
        if inplace:
            temp = data
        else:
            temp = data.copy(deep=True)

        for meta_field in fields_to_categorize:
            if meta_field in additional_info and isinstance(additional_info[meta_field], list):
                temp[meta_field] = pd.cut(temp[meta_field], bins=additional_info[meta_field])
                temp[meta_field] = temp[meta_field].cat.add_categories(["?"])
                temp[meta_field] = temp[meta_field].fillna("?")
            else:
                temp[meta_field] = temp[meta_field].replace({np.nan: "?"})
                temp[meta_field] = temp[meta_field].astype("category")

        converter = {field: dict(enumerate(temp[field].cat.categories)) for field in fields_to_categorize}

        if inplace:
            return converter
        else:
            return Data(temp, converter)

    @staticmethod
    def filter_dataframe_fields_on_values(data: pd.DataFrame, filter_values: Dict[str, List], to_keep: bool = True):
        """Filter `data` by matching targets for multiple columns.

        Args:
            data: Dataframe, slice of the total dataset.
            filter_values: Dictionary of the form: `{<field>: <target_values_list>}`
                used to filter columns data.
            to_keep: Boolean which determines whether to keep or to remove `filter_values` from `data`.
        """
        try:
            if to_keep:
                return data[np.logical_and.reduce([data[column].isin(target_values) for column, target_values in filter_values.items()])]
            else:
                return data[~np.logical_or.reduce([data[column].isin(target_values) for column, target_values in filter_values.items()])]
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def filter_dataframe_field_on_values(data: pd.DataFrame, field: str, values: List, to_keep: bool = True):
        """Filter `data` by matching targets for column `field`.

        Args:
            data: Dataframe, slice of the total dataset.
            field: Column to filter on.
            values: List if values to match `field` on.
            to_keep: Boolean which determines whether to keep or to remove `values` from `data`.
        """
        return Data.filter_dataframe_fields_on_values(data, {field: values}, to_keep)

    @staticmethod
    def filter_dataframe_field_on_value(data: pd.DataFrame, field: str, value: Any, to_keep: bool = True):
        """Filter `data` by matching targets for column `field`.

        Args:
            data: Dataframe, slice of the total dataset.
            field: Column to filter on.
            value: Value to match `field` on.
            to_keep: Boolean which determines whether to keep or to remove `value` from `data`.
        """
        return Data.filter_dataframe_field_on_values(data, field, [value], to_keep)

    @staticmethod
    def compute_window_summary(data: pd.DataFrame):
        """Compute some summary insights on a time window.
        
        Args:
            data: Dataframe, slice of the total dataset.
        """
        # TODO: Do better for 'auth_freq'
        # ISO8601 is not handled yet by datetime so as a fix we replace 'Z' by '+00:00'

        is_empty = data.shape[0] == 0
        if not is_empty:
            time = data['systemtime'].apply(lambda x: datetime.fromisoformat(str(x).replace("Z", "+00:00")))
            min_time, max_time = min(time), max(time)
            delta = max_time - min_time

        return {
            "min_time": min_time if not is_empty else 0,
            "max_time": max_time if not is_empty else 0,
            "delta": delta if not is_empty else timedelta(microseconds=0),
            "nb_auth": time.size if not is_empty else 0,
            "auth_freq": (time.size / delta.total_seconds() if delta.total_seconds() != 0 else time.size) if not is_empty else 0,
            "nb_hosts": data['host'].unique().size if not is_empty else 0,
        }

    @staticmethod
    def highlight_dataframe_fields(data: pd.DataFrame, lines: List, fields: List[str]):
        """Highlight in a red color the lines and fields asked."""
        return data.style.applymap(lambda x: "background: red", subset=pd.IndexSlice[lines, fields])
