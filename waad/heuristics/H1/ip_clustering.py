"""This module implements an IP clustering block."""


import ipaddress
import numpy as np
from sklearn.cluster import DBSCAN
from typing import List


from waad.heuristics.H1.ip_processing import IPProcessing
from waad.utils.clustering import StringClustering


class IPClustering(StringClustering):
    """This class implements an IP clustering based on a DBSCAN clustering on integer values.

    Attributes:
        ips (List[str]): List of strings to cluster.
        dbscan_eps (float): The radius of a neighborhood to consider in the DBSCAN with respect to some point.
        min_samples (int): Minimum number of samples to be considered as a core point in DBSCAN algorithm.
    """

    def __init__(self, ips: List[ipaddress.IPv4Address], dbscan_eps: float = 150, min_samples: int = 2):
        super().__init__([ip.exploded for ip in ips])
        self.ips = ips
        self.dbscan_eps = dbscan_eps
        self.min_samples = min_samples

    def run(self):
        """Group IPv4 addresses using a DBSCAN algorithm, their decimal representation and a cartesian metric."""
        X = np.array([int(ip) for ip in self.ips]).reshape(-1, 1)
        clustering = DBSCAN(eps=self.dbscan_eps, min_samples=self.min_samples).fit(X)

        clusters = {}
        for k in np.unique(clustering.labels_):
            clusters[k] = []
        for i, v in enumerate(self.ips):
            clusters[clustering.labels_[i]].append(v.exploded)

        for k, v in clusters.items():
            if k == -1:
                self.clusters[None] = v
            else:
                self.clusters[IPClustering.get_subnet_mask_from_ips(v)] = v
        self.clusters = self.merge_subnet_clusters()

    def merge_subnet_clusters(self):
        def get_biggest_subnet(L: List[ipaddress.ip_network]):
            biggest = L[0]
            for element in L:
                if biggest.subnet_of(element):  # type: ignore
                    biggest = element
            return biggest

        clusters = {k: v for k, v in self.clusters.items()}
        networks = [ipaddress.ip_network(network) for network in self.clusters if network is not None]
        to_merge = {}
        for network1 in networks:
            L = [network2 for network2 in networks if (network1 != network2 and network1.subnet_of(network2))]
            if L != []:
                to_merge[network1.exploded] = get_biggest_subnet(L).exploded

        for network1, network2 in to_merge.items():
            clusters[network2].extend(clusters[network1])
            del clusters[network1]

        return clusters

    @staticmethod
    def get_subnet_mask_from_ips(ips: List[str]):
        def common_start(sa: str, sb: str):
            """Returns the longest common substring from the beginning of sa and sb."""

            def _iter():
                for a, b in zip(sa, sb):
                    if a == b:
                        yield a
                    else:
                        return

            return "".join(_iter())

        s = bin(int(ipaddress.ip_address(ips[0])))[2:].zfill(32)
        for s_compare in [bin(int(ipaddress.ip_address(ip)))[2:].zfill(32) for ip in ips[1:]]:
            temp = common_start(s, s_compare)
            if temp != s:
                s = temp
        return f"{IPProcessing.binary_ip_to_dec(s.ljust(32, '0'))}/{len(s)}"
