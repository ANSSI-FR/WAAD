"""This module implements some machine clustering specific to H2."""


import pandas as pd
from typing import List, Set


from waad.utils.asset import Machine
from waad.utils.clustering import LongestCommonSubstringClustering


class H2SpecificClustering(LongestCommonSubstringClustering):
    """H2 very specific clustering defined with the analysts.

    Attributes:
        logontype_workstations (pd.DataFrame): Table of all distinct combinations of (logontype, workstationname).
        workstations (Set[Machine]): All distinct workstations of the dataset as `Machine` objects.
        hosts (Set[Machine]): All distinct hosts of the dataset as `Machine` objects.
        min_samples (int): Minimum samples to give as input of `LongestCommonSubstringClustering`.
        big_clusters_min_size (int): Minimum size of what is considered a 'big' cluster.
        small_clusters_max_size (int): Maximum size of what is considered a 'small' cluster.
        max_ratio_of_hosts (float): Maximum ratio of hosts
    """
    def __init__(
        self,
        logontype_workstations: pd.DataFrame,
        workstations: Set[Machine],
        hosts: Set[Machine],
        min_samples: int = 4,
        big_clusters_min_size: int = 50,
        small_clusters_max_size: int = 7,
        max_ratio_of_hosts: float = 0.5,
    ):

        self.logontype_workstations = logontype_workstations
        self.workstations = workstations
        self.hosts = hosts

        self.big_clusters_min_size = big_clusters_min_size
        self.small_clusters_max_size = small_clusters_max_size
        self.max_ratio_of_hosts = max_ratio_of_hosts

        super().__init__(list(set().union([m.name for m in self.workstations], [m.name for m in self.hosts])), min_samples)

    def run(self):
        super().run()

        temp = self.logontype_workstations[self.logontype_workstations["logontype"].isin([2, 11])]

        keys_to_remove = []
        for cluster_name, machines in self.clusters.items():
            if len(machines) >= self.big_clusters_min_size:
                keys_to_remove.append(cluster_name)
            elif self.small_clusters_max_size <= len(machines) < self.big_clusters_min_size and self.get_ratio_of_hosts(machines) > self.max_ratio_of_hosts:
                keys_to_remove.append(cluster_name)

        for key in keys_to_remove:
            if key is not None:
                del self.clusters[key]

        self.clusters = self.remove_from_clusters([machine.name for machine in self.hosts] + temp.workstationname.unique().tolist())

    def get_ratio_of_hosts(self, machines: List[str]):
        if len(machines) == 0:
            return 1
        return len([m for m in machines if m in [machine.name for machine in self.hosts]]) / len(machines)
