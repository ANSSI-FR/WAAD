"""This module implements a time series class with related methods."""


from collections import deque
from datetime import datetime, timedelta
from IPython.display import display
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple


from waad.utils.asset import Asset
from waad.utils.config import ANOMALIES_SCORES
from waad.utils.postgreSQL_utils import Table


class StatSeries:
    """This class defines a statistical series and implements some computing and plotting methods on it.

    Attributes:
        name (str): Name of the series.
        series(List[float]): Contains the actual data of the series.
    """

    def __init__(self, name: str, series: List[float]):
        self.name = name
        self.series = series
        self.anomalies: List = []

    def IQR_outlier_detection(self, factor: float = 1.5) -> List[int]:
        """Implement IQR outliers detection.

        Args:
            factor: IQR outliers detection factor (1.5 for standard method, up to 2 or 3 for only extrem outliers).
        """
        series = pd.Series(self.series)

        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        self.anomalies = series[((series < Q1 - factor * IQR) | (series > Q3 + factor * IQR))].index.values.tolist()

        return self.anomalies

    def std_outlier_detection(self, factor: float = 2) -> List[int]:
        """Implement std outliers detection.

        Args:
            factor: std outliers detection factor (2 for standard method 95%, up to 3 for only extrem outliers).

        Returns:
            A ``List`` containing indexes of outlier values detected.
        """
        series = pd.Series(self.series)

        std = series.std()
        mean = series.mean()

        self.anomalies = series[((series < mean - factor * std) | (series > mean + factor * std))].index.values.tolist()

        return self.anomalies

    def custom_outlier_detection(self, indicator_bound: Optional[float] = None, IQR_factor: float = 2, sigma_factor: float = 3):
        """Implement custom IQR detection, enriched by a std criterion to be more robust.

        Args:
            indicator_bound: Physical criterion that helps remove False Positives. For example with a series representing the number of authentications over time and containing
                a vast majority of zeros, the IQR would raise a lot of outliers even if it they only represent an increase of 2 authentications from the median (apparently 0). This
                is due to the fact that an attacker work pattern is highly non gaussiann.
            IQR_factor: IQR outliers detection factor (1.5 for standard method, up to 2 or 3 for only extrem outliers).
            sigma_factor: std outliers detection factor (2 for standard method 95%, up to 3 for only extrem outliers).

        Returns:
            A ``List`` containing indexes of outlier values detected.
        """
        series = pd.Series(self.series)

        std = series.std()
        mean = series.mean()
        median = series.median()
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        # Combination of a custom (stricter) IQR method and the 3-sigma rule. Even if distributions over time are not gaussians, this is supposed to show up outliers
        outliers = series[((series < Q1 - IQR_factor * IQR) | (series > Q3 + IQR_factor * IQR)) & ((series < mean - sigma_factor * std) | (series > mean + sigma_factor * std))].index.values.tolist()

        # Apply ``indicator_bound``
        if indicator_bound is not None:
            to_remove = []
            for index in outliers:
                if (indicator_bound > 0) and (series[index] < median + indicator_bound):
                    to_remove.append(index)
                elif (indicator_bound < 0) and (series[index] > median + indicator_bound):
                    to_remove.append(index)
            for index in to_remove:
                outliers.remove(index)

        self.anomalies = outliers

        return outliers

    def contains_isolated_values(self, percentage_null_values: int = 90) -> bool:
        """Detect if a series contains isolated values.

        Args:
            percentage_null_values: Percentage of zero values used as a threshold to evaluate if the series contains isolated points.

        Returns:
            A ``bool`` describing whether a time series contains isolated values or not.
        """
        nb_non_null_values = np.flatnonzero(self.series).size
        if nb_non_null_values < (1 - percentage_null_values / 100) * len(self.series) and len(self.series) >= 1:
            return True
        return False

    def detect_isolated_groups(self) -> List[List[int]]:
        """Detect isolated groups of values in ``time_series``.

        Returns:
            Groups of consecutive indices, corresponding to the isolated values (separated by zeros).
        """
        indices = np.flatnonzero(self.series)
        groups: List = []
        if indices.size == 0:
            return groups

        current_group = [indices[0]]
        for index in indices[1:]:
            if index - current_group[-1] == 1:
                current_group.append(index)
            else:
                groups.append(current_group)
                current_group = [index]
        return groups

    def detect_abnormal_outbreak(self, legitimate_model_duration: int = 50):
        """Detect if there is an abnormal outbreak values in ``time_series`` if the first
        `legitimate_model_duration` percentage of the series is zero."""
        index = next((i for i, x in enumerate(self.series) if x), None)
        if index is not None and index > legitimate_model_duration / 100 * len(self.series):
            self.anomalies = [index]

    @staticmethod
    def detect_abnormal_outbreak_static(series: List[float], legitimate_model_duration: int = 50):
        """Detect if there is an abnormal outbreak values in ``time_series`` if the first
        `legitimate_model_duration` percentage of the series is zero."""
        index = next((i for i, x in enumerate(series) if x), None)
        if index is not None and index > legitimate_model_duration / 100 * len(series):
            return [index]
        else:
            return []

    def compute_anomalies(self, anomalies_detector: Optional[Callable] = None, config: Optional[Dict[str, Dict]] = None):
        if anomalies_detector is not None:
            self.anomalies = anomalies_detector(self.series)

        else:
            if config is not None:
                self.custom_outlier_detection(indicator_bound=config[self.name]["indicator_bound"])
            else:
                self.custom_outlier_detection()

    def plot_series(self, ax: Axes):
        """Plot a series.

        Examples:
            >>> import matplotlib.pyplot as plt
            >>> import numpy as np
            >>> from waad.utils.indicators import plot_series
            >>>
            >>> data = [355, 368,   0,   0,   0, 447, 466, 250, 367,   0,   0,   0, 320,
                        307, 395, 601, 258,   0,   0,   0, 382, 400, 326, 319,   0,   0,
                        304, 360, 327, 368,   0,   0,   0, 383, 327, 422, 290, 253,   0,
                        0, 446, 414, 381, 393,   0,   0,   0,   0, 373, 387, 312, 327,
                        0,   0, 370, 275, 436, 348]
            >>>
            >>> demo = StatSeries('demo', data)
            >>> fig, ax = plt.subplots(figsize=(30, 5))
            >>> demo.plot_series(ax)

            .. testcleanup::

                fig.savefig(f'{DOCTEST_FIGURES_PATH}/test.png')

            .. figure:: ../../_static/doctest_figures/time_series_plot_example.png
                :align: center
                :alt: time series plot example

        Args:
            ax: ``Axes`` to plot series on.
        """
        ax.plot([i for i in range(1, len(self.series) + 1)], self.series)
        ax.set_title(self.name)

    def get_figure(self, figsize: Tuple[int, int] = (20, 4)) -> Figure:
        fig, ax = plt.subplots(figsize=figsize)
        self.plot_series(ax)
        return fig

    def display(self):
        fig = self.get_figure()
        fig.axes[0].vlines(np.array(self.anomalies) + 1, *fig.axes[0].get_ylim(), colors="r")
        display(fig)


class TimeSeries(StatSeries):
    """This class is a child of ``StatSeries`` taking into account a notion of time.

    Attributes:
        time_step (float): Time step in seconds between each index.
        start_time (Optional[str]): Start time of the series in ISO format.
        intermediary_content (Optional[Any]): Helper that keeps in memory intermediary content used during previous computations.
    """

    def __init__(self, name: str, series: List[float], time_step: float, start_time: Optional[str] = None, intermediary_content: Optional[Any] = None):
        super().__init__(name, series)
        self.time_step = time_step
        self.start_time = start_time
        self.intermediary_content = intermediary_content

    def get_anomalies_date(self):
        res = []
        for anomaly in self.anomalies:
            try:
                start = datetime.fromisoformat(self.start_time) + timedelta(seconds=self.time_step * anomaly)
                end = start + timedelta(seconds=self.time_step)
                res.append(f'{start.isoformat()} - {end.isoformat()}')
            except Exception as e:
                print(e)
                pass
        return res

    def detailed_display(self):
        self.display()
        anomalies_date = self.get_anomalies_date()
        for i, anomaly in enumerate(self.anomalies):
            print(f"Anomaly found at time step {anomaly} / {anomalies_date[i]}")
            print(f"Pic value of {self.series[anomaly]} on indicator")
            if self.intermediary_content is not None:
                print(f"Intermediary content : {self.intermediary_content[anomaly]}")
            print()
