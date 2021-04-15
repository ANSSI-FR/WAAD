"""This module implements the computation of some indicators on assets."""


import bisect
from datetime import datetime, timedelta
from enum import Enum
from functools import partial
import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import Any, Callable, Dict, List, Optional


from waad.utils.asset import Asset
from waad.utils.config import ANOMALIES_SCORES
from waad.utils.postgreSQL_utils import Table
from waad.utils.rule import Rule
from waad.utils.time_series_utils import StatSeries, TimeSeries


class Indicator:    
    """Defines an `Indicator` on a StatSeries and the conditions for which it applies.

    Attributes:
        name (str): Name of the indicator to compute.
        additional_columns (List[str]): Initially, only 'systemtime' is requested alongside with asset_1 and asset_2 see `ComputeIndicators` down below.
            All columns from `additional_columns` will be requested as well if needed in an `Indicator`.
        step_by_step_computation (Callable): For each `time_step`, all asset_1 corresponding authentication are gathered and `step_by_step_computation`
            is applied on the corresponding authenticaions dataframe. Exemples of such functions are : lambda window: window.shape[0] (to get number of asset_1
            authentications for every time_step), lambda window: set(window['asset_2'].unique()) (to get all distinct asset_2 reached per `time_step` under 
            the rule), get_privileges(window: pd.DataFrame) defined down below to get all distinct privileges granted per `time_step`. `step_by_step_computation`
            must be a function taking as input a window of authentications as built in `ComputeIndicators` and return a float for each `time_step`.
        intermediary_content_function (Optional[Callable]): After `step_by_step_computation` we are left with a list of float for each `time_step`. 
            If `intermediary_content_function` is `None`, Timeseries.intermediary_content will be set to None. Else, `intermediary_content_function` is applied 
            on the list to compute Timeseries.intermediary_content. For example, in the case of 'nb_new_assets_reached', after `step_by_step_computation` we
            are left with the list of all asset_2 reached at each `time_step`, with `intermediary_content_function` we want to keep in memory the new assets reached
            at each `time_step`. `intermediary_content_function` must be a function taking as input a list of floats and returning something from it (if we want exactly
            the output of `step_by_step_computation`, just write identity lambda x: x).
        time_series_function (Optional[Callable]): This function populates the attibute `series` of the `Timeseries` returned after computation. If None, it uses 
            the result of `step_by_step_computation` as a result, else it takes as an input the output of `step_by_step_computation` and returns a list, computed 
            from it. `time_series_function` must be either `None` or a function taking as input a list and returning a list from the same size.
        anomalies_detector (Optional[Callable]): This function defines how to compute possible anomalies on the `StatSeries` corresponding to the indicator. If 
            `None`, the StatSeries.custom_outlier_detection wil be used with parameters correponding to the indicator written in config.py. Else, `anomalies_detector`
            must be a function taking as an input the StatSeries.series and returning the possible anomalies detected in a list of indices.
    """

    def __init__(self, 
        name: str, 
        additional_columns: List[str] = [], 
        step_by_step_computation: Callable = lambda window: window.shape[0], 
        intermediary_content_function: Optional[Callable] = None,
        time_series_function: Optional[Callable] = None,
        anomalies_detector: Optional[Callable] = None
    ):

        self.name = name
        self.additional_columns = additional_columns
        self.step_by_step_computation = step_by_step_computation
        self.intermediary_content_function = intermediary_content_function
        self.time_series_function = time_series_function
        self.anomalies_detector = anomalies_detector
    
    def __repr__(self):
        return self.name


class ComputeIndicators:
    """This class defines a framework to compute timeseries indicators from a dataset.

    Attributes:
        table (Table): `Table` object pointing to the postgreSQL dataset.
        rule (Rule): `Rule` object defining how to filter dataset rows based on analysts' requirements.
        time_step (int): Time step in between each time series tick.
        indicator_objects (List[Indicator]): List of all types of indicators we want to compute for each asset_1 object.
    """

    def __init__(self, table: Table, rule: Rule, indicator_objects: List[Indicator], time_step: int = 86400):
        self.table = table
        self.rule = rule
        self.indicator_objects = indicator_objects
        self.time_step = time_step

        self.indicators: Dict[Asset, Dict[Indicator, TimeSeries]] = {}

    def run(self):
        cache = {}
        additional_columns = [e for indicator in self.indicator_objects for e in indicator.additional_columns]

        def update_cache(row: List, dataset_columns: List[str], condition: Dict):
            row = {col: value for col, value in zip(dataset_columns, row)}
            
            if condition['filter_function'](row):
                asset_1 = condition['asset_1'](row)
                asset_2 = condition['asset_2'](row)
                
                line_summary = {'systemtime': row['systemtime'], 'asset_2': asset_2}
                line_summary.update({col: row[col] for col in additional_columns})

                try:
                    cache[asset_1].append(line_summary)
                except Exception:
                    cache[asset_1] = [line_summary]

        for condition in self.rule.conditions:
            sql_command = self.table.custom_psql_request({'fields_to_request': '*', 'filters': [condition['pre_filters']]})
            cursor = self.table.database.get_iterator_from_command(sql_command, chunk_size=1000000)
            row_0 = next(cursor)
            columns = [desc[0] for desc in cursor.description]

            update_cache(row_0, columns, condition)

            for row in cursor:
                update_cache(row, columns, condition)
            cursor.close()
        self.table.database.disconnect()

        for asset, asset_authentications in cache.items():
            self.indicators[asset] = ComputeIndicators.compute_indicators_over_time(
                pd.DataFrame(asset_authentications), indicators=self.indicator_objects, time_step=self.time_step
            )  

    @staticmethod
    def compute_new_items(items_sets: List[set], legitimate_model_duration: int = 25, enrich_model=True):
        """Compute the new items reached from a list of ``items_sets``.
            This is usable for example to compute the number of new computers reached or the number of new privileges granted.

        Args:
            items_sets: List of all items reached ``time_step`` after ``time_step``.
            legitimate_model_duration: Percentage of the dataset used to build the corresponding legitimate model for items reached.
            enrich_model: Boolean to know if after ``legitimate_model_duration`` new items are used to enrich the legitimate model.

        Returns:
            The new items reached ``time_step`` after ``time_step``.
        """

        new_items: List[set] = []
        legitimate_model = set()

        for index, items in enumerate(items_sets):
            if index <= int(legitimate_model_duration / 100 * len(items_sets)):
                new_items.append(set())
                legitimate_model.update(items)
            else:
                new_items.append(items.difference(legitimate_model))
                if enrich_model:
                    legitimate_model.update(items)

        return new_items

    @staticmethod
    def compute_nb_new_items(items_sets: List[set], legitimate_model_duration: int = 25, enrich_model=True):
        """Compute the number of new items reached from a list of ``items_sets``.
            This is usable for example to compute the number of new computers reached or the number of new privileges granted.

        Args:
            items_sets: List of all items reached ``time_step`` after ``time_step``.
            legitimate_model_duration: Percentage of the dataset used to build the corresponding legitimate model for items reached.
            enrich_model: Boolean to know if after ``legitimate_model_duration`` new items are used to enrich the legitimate model.

        Returns:
            The number of new items reached ``time_step`` after ``time_step``.
        """
        return [len(e) for e in ComputeIndicators.compute_new_items(items_sets=items_sets, legitimate_model_duration=legitimate_model_duration, enrich_model=enrich_model)]

    @staticmethod
    def get_privileges(window: pd.DataFrame):
        res = set()
        window['privilegelist'].apply(lambda x: res.update(set(x.split(':'))))
        try:
            res.remove('?')
        except Exception:
            pass
        return res

    @staticmethod
    def compute_indicators(window: pd.DataFrame, indicators: List[Indicator]) -> Dict:
        """Compute some indicators over ``window``.

        Args:
            window: Pandas ``Dataframe``, slice of the dataset.
            indicators: List containing the ``Indicator`` objects.

        Returns:
            A dictionnary containing the indicators computed on ``window``.
        """
        return {indicator: indicator.step_by_step_computation(window) for indicator in indicators}

    @staticmethod
    def compute_indicators_over_time(data: pd.DataFrame, indicators: List[Indicator], time_step: int = 86400):
        """Compute some indicators over time, should be way faster because it uses `bisect` search.

        Args:
            data: Pandas ``Dataframe``, part of the dataset.
            indicators_name: List containing the names of indicators needed.
            time_step: Time step in seconds desired between each loop of indicators computation.

        Returns:
            A dictionnary containing the indicators computed on each time ``window``.
        """
        step_by_step_results = {indicator: [] for indicator in indicators}

        # TODO: Implement better inclusion of a posteriori indicators
        if data.shape[0] == 0:
            return [TimeSeries(name=indicator.name, series=[], time_step=time_step) for indicator in indicators]

        # ISO8601 is not handled yet by datetime so as a fix we replace 'Z' by '+00:00'
        data = data.sort_values("systemtime")
        data.reset_index(drop=True, inplace=True)

        is_iso8601 = "Z" in data["systemtime"][0]
        if is_iso8601:
            data["systemtime"] = data["systemtime"].apply(lambda x: str(x).replace("Z", "+00:00").replace("T", " "))

        start_time = data.systemtime.iloc[0]
        end_time = data.systemtime.iloc[-1]

        current_time = start_time
        current_index = 0

        while current_time < end_time:

            to_insert = (datetime.fromisoformat(current_time) + timedelta(seconds=time_step)).isoformat().replace("T", " ")
            index = bisect.bisect_left(data.systemtime, to_insert, lo=current_index)

            window = data.iloc[current_index:index]

            window_indicators = ComputeIndicators.compute_indicators(window, indicators=indicators)
            for indicator, v in window_indicators.items():
                step_by_step_results[indicator].append(v)

            current_index = index
            current_time = to_insert

        res = {}
        for indicator in indicators:
            intermediary_content = None
            series = step_by_step_results[indicator]
            if indicator.intermediary_content_function is not None:
                intermediary_content = indicator.intermediary_content_function(series)
            if indicator.time_series_function is not None:
                series = indicator.time_series_function(intermediary_content)

            res[indicator] = TimeSeries(name=indicator.name, series=series, time_step=time_step, start_time=start_time, intermediary_content=intermediary_content)
        return res


class Indicators(Enum):
    """Enum to associate an indicator to its corresponding function."""

    NB_AUTHENTICATIONS = Indicator(name='nb_authentications', step_by_step_computation=lambda window: window.shape[0])

    NB_ASSETS_REACHED = Indicator(
        name='nb_assets_reached', 
        step_by_step_computation=lambda window: set(window['asset_2'].unique()), 
        intermediary_content_function=lambda x: x, 
        time_series_function=lambda x: [len(e) for e in x]
    )

    NB_NEW_ASSETS_REACHED = Indicator(
        name='nb_new_assets_reached', 
        step_by_step_computation=lambda window: set(window['asset_2'].unique()), 
        intermediary_content_function=lambda x: ComputeIndicators.compute_new_items(x, ANOMALIES_SCORES['nb_new_assets_reached']['legitimate_model_duration']), 
        time_series_function=lambda x: ComputeIndicators.compute_nb_new_items(x, ANOMALIES_SCORES['nb_new_assets_reached']['legitimate_model_duration'])
    )

    NB_PRIVILEGES_GRANTED = Indicator(
        name='nb_privileges_granted', 
        additional_columns=['privilegelist'],
        step_by_step_computation=ComputeIndicators.get_privileges, 
        intermediary_content_function=lambda x: x, 
        time_series_function=lambda x: [len(e) for e in x], 
        anomalies_detector=lambda series: StatSeries.detect_abnormal_outbreak_static(series, ANOMALIES_SCORES['nb_privileges_granted']['legitimate_model_duration'])
    )
