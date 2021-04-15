"""This module implements some facilities to combine FaitNotable together."""


from IPython.display import display
from IPython.display import Markdown
import pandas as pd
from typing import Callable, Dict, List


from waad.utils.asset import Asset
from waad.utils.fait_notable import FaitNotable


class AnomalousAsset:
    """This class defines an `AnomalousAsset`.

    Attributes:
        asset (Asset): Asset concerned.
        anomaly_score (float): Abnormality score of the `Asset`.
        faits_notables (List[FaitNotable]): List of `FaitNotable` attributed to the `asset`.
    """

    def __init__(self, asset: Asset, faits_notables: List[FaitNotable] = []):
        self.asset = asset
        self.faits_notables: List[FaitNotable] = []
        self.anomaly_score = 0.0

        for fait_notable in faits_notables:
            self.update(fait_notable)

    def __repr__(self):
        return repr(self.asset) + f" - {self.anomaly_score}"

    def update(self, fait_notable: FaitNotable):
        self.faits_notables.append(fait_notable)
        self.anomaly_score += fait_notable.anomaly_score

    def display(self):
        print(f"{repr(self.asset)} - total anomaly score: {self.anomaly_score}")
        print("-----------")
        for fait_notable in self.faits_notables:
            fait_notable.display()
        display(Markdown("-----"))

    def detailed_display(self):
        print(f"{repr(self.asset)} - total anomaly score: {self.anomaly_score}")
        print("-----------")
        for fait_notable in self.faits_notables:
            try:
                fait_notable.detailed_display()
            except Exception:
                fait_notable.display()
        display(Markdown("-----"))


class ComputeAnomalousAssets:
    """This class is a pipeline that computes all `AnomalousAsset` from a list of `FaitNotable`.

    Attributes:
        faits_notables (List[FaitNotable]): Fields of data to combine into tuples for analysis.
        compare (Dict[Asset, Callable]): Dictionnary containing methods to compare assets between each other.
            each key must be a child of `Asset` and must take as input 2 elements and return a `bool`. If no compare 
            method is specified for a child of `Asset`, the traditional __eq__ method will be used.
        anomalous_assets (List[AnomalousAsset]): Score of abnormality of the `Asset`.

    .. code-block:: python

        compare = {
            Machine: lambda m1, m2: m1.name == m2.name,
            Account: lambda a1, a2: a1.sid == a2.sid
        }
    """

    def __init__(self, faits_notables: List[FaitNotable], compare: Dict[Asset, Callable] = {}):
        self.faits_notables = faits_notables
        self.compare = compare

        self.anomalous_assets: List[AnomalousAsset] = []

    def run(self):
        for fait_notable in self.faits_notables:
            for asset in fait_notable.assets_concerned:
                is_inside = False
                for aa in self.anomalous_assets:
                    try:
                        if isinstance(aa.asset, type(asset)) and self.compare[type(asset)](asset, aa.asset):
                            is_inside = True
                            aa.update(fait_notable)
                    except Exception:
                        if asset == aa.asset:
                            is_inside = True
                            aa.update(fait_notable)
                
                if not is_inside:
                    self.anomalous_assets.append(AnomalousAsset(asset, [fait_notable]))

        self.anomalous_assets.sort(key=lambda x: x.anomaly_score, reverse=True)

    def get_summary(self) -> pd.DataFrame:
        return pd.DataFrame([[repr(aa.asset), aa.anomaly_score] for aa in self.anomalous_assets], columns=["anomalous_asset", "anomaly_score"])
