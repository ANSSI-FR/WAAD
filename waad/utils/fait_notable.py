"""This module implements a framework for rare events called `FaitNotable` with some facilities."""


import ipaddress
from IPython.display import display
from tqdm import tqdm
from typing import Any, Dict, List, Optional


from waad.utils.asset import Asset, IP, Machine
from waad.utils.config import ANOMALIES_SCORES
from waad.utils.indicators import Indicator, Indicators
from waad.utils.postgreSQL_utils import Table
from waad.utils.time_series_utils import StatSeries
from waad.utils.single_tuple_analyser import SingleTupleAnalyser
from waad.utils.tuples_analyser import AnalystTuplesAnalyser


class FaitNotable:
    """This class defines a `FaitNotable`.

    Attributes:
        anomaly_score (float): Abnormality score of the anomaly.
        assets_concerned (List[FaitNotable]): All assets concerned by the anomaly.
        reason (Optional[str]): A short explanation of the anomaly.
        content (Optional[Any]): Some interpretability content of the anomaly. 
    """

    def __init__(self, anomaly_score: float, assets_concerned: List[Asset], reason: Optional[str] = None, content: Optional[Any] = None):
        self.anomaly_score = anomaly_score
        self.reason = reason
        self.assets_concerned = assets_concerned
        self.content = content

    def display(self):
        print(self.assets_concerned)
        print(self.reason)
        print(self.anomaly_score)
        if self.content is not None:
            try:
                self.content.display()
            except Exception:
                display(self.content)

    def detailed_display(self):
        print(self.assets_concerned)
        print(self.reason)
        print(self.anomaly_score)
        if self.content is not None:
            try:
                self.content.detailed_display()
            except Exception:
                try:
                    self.content.display()
                except Exception:
                    display(self.content)


class ComputeFaitsNotables:
    """This parent class gives a common framework for all computation of `FaitNotable`.

    Attributes:
        config (Dict): Config dict containing all scores and parameters of anomalies by type.
        faits_notables (List[FaitNotable]): All `FaitNotable` concerned by the anomaly.
    """

    def __init__(self):
        self.config = None
        self.faits_notables = []

    def run(self):
        try:
            self.config = ANOMALIES_SCORES
        except Exception as e:
            print(e)
            pass


class ComputeFaitNotablesFromRareIPv6(ComputeFaitsNotables):
    """This class implements the computation of `FaitNotable` for rare IPv6s.

    Attributes:
        ipv6s (List[ipaddress.IPv6Address]): List of all ipv6s in the dataset.
        ipv4s (List[ipaddress.IPv4Address]): List of all ipv4s in the dataset.
        min_ipv6_ratio (float): If ipv6 ratio on the dataset is under `min_ipv6_ratio` then a `FaitNotable` is risen.
    """

    def __init__(self, ipv6s: List[ipaddress.IPv6Address], ipv4s: List[ipaddress.IPv4Address], min_ipv6_ratio: float = 0.02):
        super().__init__()
        self.ipv6s = ipv6s
        self.ipv4s = ipv4s
        self.min_ipv6_ratio = min_ipv6_ratio

    def run(self):
        super().run()
        ratio = len(self.ipv6s) / len(self.ipv4s) if len(self.ipv4s) != 0 else -1

        if 0 < ratio < self.min_ipv6_ratio and self.config is not None:
            for ipv6 in self.ipv6s:
                self.faits_notables.append(
                    FaitNotable(
                        anomaly_score=self.config["rare_use_IPv6"]["score"],
                        assets_concerned=[IP(ipv6.exploded)],
                        reason="Low ratio of IPv6",
                        content=None,
                    )
                )


class ComputeFaitNotablesFromAnalystTuplesAnalysers(ComputeFaitsNotables):
    """This class implements the computation of `FaitNotable` for rare tuples found via `AnalystTuplesAnalyser`.

    Attributes:
        tuples_analysers (Dict[Asset, AnalystTuplesAnalyser]): Dictionary containing `AnalystTuplesAnalyser` per `Asset`.
    """

    def __init__(self, tuples_analysers: Dict[Asset, AnalystTuplesAnalyser]):
        super().__init__()
        self.tuples_analysers = tuples_analysers

    def run(self):
        super().run()

        if self.config is not None:
            for asset, ata in self.tuples_analysers.items():
                # if ata.candidate is not None:    # Better to filter on those actually containing a candidate ?
                self.faits_notables.append(
                    FaitNotable(
                        anomaly_score=self.config["rare_grouping_events"]["score"],
                        assets_concerned=[asset],
                        reason=f"{repr(asset)} with rare grouping of events.",
                        content=ata.candidate.get_summary() if ata.candidate is not None else None,
                    )
                )


class ComputeFaitNotablesFromIndicators(ComputeFaitsNotables):
    """This class implements the computation of `FaitNotable` from indicators containing anomalies.

    Attributes:
        indicators (Dict[Asset, Dict[Indicator, StatSeries]]): Dictionary containing indicators computed and classified 
            per `Asset` and the per `Indicator`.
    """

    def __init__(self, indicators: Dict[Asset, Dict[Indicator, StatSeries]]):
        super().__init__()
        self.indicators = indicators

    def run(self):
        super().run()

        for asset, indicators_dict in tqdm(list(self.indicators.items())):
            for indicator, series in indicators_dict.items():
                series.compute_anomalies(anomalies_detector=indicator.anomalies_detector, config=self.config)
                if series.anomalies != []:
                    self.faits_notables.append(
                        FaitNotable(
                            anomaly_score=self.config[indicator.name]["score"],
                            assets_concerned=[asset],
                            reason=f"Abnormal behavior of {asset.__class__.__name__} on indicator {indicator.name}.",
                            content=series,
                        )
                    )
        
            if len(indicators_dict) > 1 and len(set.intersection(*[set(series.anomalies) for indic, series in indicators_dict.items() if indic != Indicators.NB_PRIVILEGES_GRANTED.value])) > 0:
                    self.faits_notables.append(
                        FaitNotable(
                            anomaly_score=self.config["corresponding_anomalies_on_all_indicators"]["score"],
                            assets_concerned=[asset],
                            reason=f"Abnormal behavior of {asset.__class__.__name__} on all indicators for the same time stamp.",
                            content=None,
                        )
                    )


class ComputeFaitNotablesFromIsolatedMachines(ComputeFaitsNotables):
    """This class implements the computation of `FaitNotable` for isolated machines in H2.

    Attributes:
        clusters (Dict[str, List[str]]): Dictionary containing machines classified with a clustering method.
    """

    def __init__(self, clusters: Dict[str, List[str]]):
        super().__init__()
        self.clusters = clusters

    def run(self):
        super().run()
        score = self.config["isolated_workstation_name_h2"]["score"]

        if self.config is not None:
            for cluster_name, machines in self.clusters.items():
                for machine in machines:
                    self.faits_notables.append(
                        FaitNotable(
                            anomaly_score=score,
                            assets_concerned=[Machine(name=machine)],
                            reason="Isolated machine after H2 specific clustering",
                            content=None,  # Maybe put all clusters inside so that we can plot them ?
                        )
                    )


class ComputeFaitNotablesFromWINMachine(ComputeFaitsNotables):
    """This class implements the computation of `FaitNotable` for WIN* machines in H2.

    Attributes:
        WIN_machines (List[str]): List of all WIN* machines to score.
        table (Table): `Table` object pointing to the postgreSQL dataset.
    """

    def __init__(self, WIN_machines: List[str], table: Table):
        super().__init__()
        self.WIN_machines = WIN_machines
        self.table = table

    def run(self):
        super().run()

        if self.config is not None:
            for wkname in self.WIN_machines:
                win_authentications = self.table.get_field_filtered_on_value("WorkstationName", wkname)
                sta = SingleTupleAnalyser(win_authentications, fields=["processname", "host", "eventid", "targetusername"])
                sta.run()
                self.faits_notables.append(
                    FaitNotable(
                        anomaly_score=self.config["WIN_default_machine_name"]["score"],
                        assets_concerned=[Machine(name=wkname)],
                        reason="WIN* default machine name",
                        content=sta.get_summary(),
                    )
                )


class ComputeFaitNotablesFromDESKTOPMachine(ComputeFaitsNotables):
    """This class implements the computation of `FaitNotable` for DESKTOP* machines in H2.

    Attributes:
        DESKTOP_machines (List[str]): List of all DESKTOP* machines to score.
        table (Table): `Table` object pointing to the postgreSQL dataset.
    """

    def __init__(self, DESKTOP_machines: List[str], table: Table):
        super().__init__()
        self.DESKTOP_machines = DESKTOP_machines
        self.table = table

    def run(self):
        super().run()

        if self.config is not None:
            for wkname in self.DESKTOP_machines:
                desktop_authentications = self.table.get_field_filtered_on_value("WorkstationName", wkname)
                sta = SingleTupleAnalyser(desktop_authentications, fields=["processname", "host", "eventid", "targetusername"])
                sta.run()
                self.faits_notables.append(
                    FaitNotable(
                        anomaly_score=self.config["DESKTOP_machine_name"]["score"],
                        assets_concerned=[Machine(name=wkname)],
                        reason="DESKTOP* default machine name",
                        content=sta.get_summary(),
                    )
                )


class ComputeFaitNotablesFromH2SpecificClustering(ComputeFaitsNotables):
    """This class implements the computation of `FaitNotable` for machines in H2. 

    Attributes:
        clusters (Dict[Optional[str], List[str]]): All clusters after `H2SpecificClustering`.
        table (Table): `Table` object pointing to the postgreSQL dataset.
    """

    def __init__(self, clusters: Dict[Optional[str], List[str]], table: Table):
        super().__init__()
        self.clusters = clusters
        self.table = table

    def run(self):
        cfnfim = ComputeFaitNotablesFromIsolatedMachines(self.clusters)
        cfnfim.run()
        self.faits_notables.extend(cfnfim.faits_notables)

        cfnfwm = ComputeFaitNotablesFromWINMachine(self.get_machines_with_pattern("WIN"), self.table)
        cfnfwm.run()
        self.faits_notables.extend(cfnfwm.faits_notables)

        cfnfdm = ComputeFaitNotablesFromDESKTOPMachine(self.get_machines_with_pattern("DESKTOP"), self.table)
        cfnfdm.run()
        self.faits_notables.extend(cfnfdm.faits_notables)

    def get_machines_with_pattern(self, pattern: str):
        for k in self.clusters:
            if k is not None and (pattern in k or pattern.lower() in k):
                return self.clusters[k]
        if None in self.clusters:
            res = []
            for machine in self.clusters[None]:
                if pattern in machine or pattern.lower() in machine:
                    res.append(machine)
            return res
        else:
            return []
