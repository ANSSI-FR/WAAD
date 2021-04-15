"""This module implements some clustering related functions."""


from difflib import SequenceMatcher
from IPython.display import display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import Callable, Dict, List, Optional
from wordcloud import WordCloud


from waad.utils.asset import Asset


class StringClustering:
    """This class defines a framework for string clustering. It implements some common methods and plotting facilities.

    Attributes:
        strings (List[str]): List of strings to cluster.
        clusters(Dict[str, List[str]]): Contains the actual computed clusters.
    """

    def __init__(self, strings: List[str]):
        self.strings = strings
        self.clusters: Dict = {}

    def run(self):
        pass

    def remove_from_clusters(self, to_remove: List[str]) -> Dict[str, List[str]]:
        res = {key: [v for v in value] for key, value in self.clusters.items()}

        for element in to_remove:
            for k, v in res.items():
                if element in v:
                    v.remove(element)
        return res

    @staticmethod
    def plot_clusters_static(clusters: Dict[str, List[str]], save: bool = False, path: str = "./"):
        """Plot string clusters in a wordcloud way. See documentation down below."""
        total_nb_clusters = len(clusters)
        if total_nb_clusters > 50:
            print(f"There are too many clusters ({total_nb_clusters}), only the first 50 will be displayed")

        nb_clusters = min(total_nb_clusters, 50)

        fig, ax = plt.subplots(ncols=nb_clusters, figsize=(nb_clusters * 8, 8))
        if nb_clusters == 1:
            ax = [ax]
        for index, (key, values) in enumerate([items for items in clusters.items()][:nb_clusters]):
            freq = {}
            for element in values:
                freq[element] = 1

            if len(values) > 0:
                wordcloud = WordCloud(width=800, height=800, background_color="white", min_font_size=8, prefer_horizontal=1)
                wordcloud.generate_from_frequencies(frequencies=freq)

                # plot the WordCloud image
                ax[index].imshow(wordcloud)

            else:
                ax[index].plot(ax[index].get_xlim(), ax[index].get_ylim(), ls="-", color="black")

            ax[index].axis("off")
            ax[index].set_title(f"Cluster '{key}' - {len(values)} items")

        fig.tight_layout(pad=2.0)
        if save:
            fig.savefig(path + "clustering.png")

        return fig

    def plot_clusters(self, save: bool = False, path: str = "./"):
        """Plot some clusters.

        Examples:
            >>> from waad.utils.indicators import plot_series
            >>>
            >>> strings = ['acr-01', 'acr-02', 'acr-03', 'acr-04', 'adm-01', 'adm-02', 'adm-03', 'adm-05', 'adm-06', 'adm-07', 'ar1-01', 'ar1-03',
            'ar4-01', 'arm-01', 'arm-02', 'arm-pa-01', 'arm-pa-02', 'ar-pa-01', 'ar-pa-02', 'ar-pa-03', 'bb-01', 'bb-02', 'bb-03', 'bb-04',
            'bb-05', 'bb-07', 'bb-08', 'bb-09', 'bb-10', 'bb-pa-01', 'bb-pa-03', 'cedre6', 'cedre7', 'cedre8', 'chrte-lab', 'cz12e9a',
            'dellbob', 'des00012', 'desk1200', 'desk1211', 'desk1417', 'desk1478', 'desk1480', 'desk1481', 'desk1488', 'desk1495',
            'desk1498', 'desk1598', 'desk1817', 'desk1821', 'desk1825', 'desk1827', 'diskWKS', 'elk-01', 'elk-02', 'frank-PC', 'hlp-01',
            'hlp-04', 'hlp-05', 'hlp-pa-01', 'infor-01', 'jdg-PC', 'labotest', 'lap0000015', 'lap0000503', 'lap0000514', 'lap0000802',
            'lap0000871', 'lap0000990', 'lap0000990', 'lap0001481', 'lap0008044', 'lap0008162', 'lap0008215', 'lap0008471',
            'lap0008543', 'lap0008884', 'lap0009033', 'lap0009213', 'lap0009327', 'lap0009376', 'lap0009461', 'lap0009596',
            'lap0009671', 'lap0009751', 'lap0009777', 'lap0009790', 'lap0009800', 'lap0009841', 'lap0009864', 'lap0009978',
            'lap1110310', 'lap1111528', 'lap1112330', 'lap1112927', 'lap1113101', 'lap1113617', 'lap1115550', 'lap1119902',
            'lenovo-marcel', 'mac-jean', 'mickael-pc', 'NPKC', 'portb-01', 'portb-02', 'portb-03', 'portb-05', 'portb-06', 'pow151',
            'pow152742', 'pow153743', 'pow158870', 'pr1376', 'pr1499', 'pr1593', 'pr1600', 'pr1605', 'pr2aerra2', 'pr2azara2',
            'ps2aacra2', 'ps2adgra2', 'qa1001E', 'qa1002C', 'qa1025F', 'qa1026R', 'qa1783A', 'serveurwin2k16', 'shkengineering-w-01',
            'shken-w-003', 'shken-w-004-pc', 'shken-w-009', 'siem-01', 'siem-02', 'siem-03', 'sqlsrv2k16', 'tabazk32', 'tabazk87',
            'windc', 'windows7-pc', 'winltp11', 'wkeng-u-005', 'wkeng-w-001', 'wkeng-w-002', 'wkeng-w-003', 'wkeng-w-006', 'wkeng-w-007',
            'wkeng-w-009', 'wkeng-w-010', 'wkeng-w-011', 'wst000001', 'wst000002', 'wst000010', 'wst000011', 'wst000012', 'wst000013',
            'wst000016', 'wst000024', 'wst000026', 'wst16001', 'wst16033', 'wst16054', 'wst16062', 'wst16071', 'wst16072', 'wst16074',
            'wst16084', 'wst16086', 'wst16087', 'wst16088', 'wst16089', 'wst16092', 'wst16095', 'wst16096', 'zag-laptop']
            >>>
            >>> lcsc = LongestCommonSubstringClustering(strings, min_samples=3, min_prefix_suffix_size=3, min_inside_size=4)
            >>> lcsc.run()
            >>> lcsc.plot_clusters()

            .. figure:: ../../_static/doctest_figures/clustering.png
                :align: center
                :alt: Clustering plot example (cropped to fit windows)

        Args:
            save: ``bool`` whether or not to save figure.
            path: ``str`` path to save figure in.
        """
        return StringClustering.plot_clusters_static(self.clusters, save, path)


class LongestCommonSubstringClustering(StringClustering):
    """This class implements an analyst approach on strings clustering.

    Attributes:
        strings (List[str]): List of strings to cluster.
        min_samples (int): Minimum samples to consider to have a consistent cluster.
        min_prefix_suffix_size (int): Minimum size of prefix or suffix pattern to be considered.
        min_inside_size (int): Minimum pattern size to be considered in the middle of a string.
    """

    def __init__(self, strings: List[str], min_samples: int = 4, min_prefix_suffix_size: int = 3, min_inside_size: int = 4):

        super().__init__(strings)
        self.min_samples = min_samples
        self.min_prefix_suffix_size = min_prefix_suffix_size
        self.min_inside_size = min_inside_size

    def run(self):
        r"""Run the algorithm.

        Explanations :
            .. figure:: ../../_static/doctest_figures/longest_common_substring_clustering.png
                :align: center
                :alt: Clustering plot example (cropped to fit windows)

            The input parameters are min_samples (the minimum number of elements needed to form a cluster) and min_pattern_size 
            (the minimum size of the character string that characterizes a cluster). Then the algorithm is as follows:

            1. Computation of the matrix of the longest common patterns (symmetric matrix therefore n^2 / 2 computation).

            2. Differentiated groupings between prefixes, suffixes and insiders: we take the column or the row corresponding 
            to if in the previous matrix, we remove all the common patterns of size less than min_pattern_size and we classify 
            them together if they are prefixes, suffixes or insider patterns.

            3. Get best key: for each string, we select the ”best key” according to the criteria described in the figure above. 
            In this case, an advantage is given to selecting a prefix over suffixes and insider patterns. This is a criterion requested 
            by the customer because prefixes are used more often. On the other hand, it is the smallest root pattern that is used because
            it allows more elements to be grouped together, even if it means proposing a new grouping that is more to grow on the newly 
            formed cluster.

            4. Grouping of best keys to form coherent clusters: we group the best keys of each string together. If a pattern contains more 
            than min_samples elements then a cluster is formed with the associated strings.

            5. Second wave (recovery of elements from the 'None' cluster): because of the arbitrary choice of the minimum in the get_best_key()
            function, certain pathological cases may appear in the 'None' cluster, in particular if a prefix which has not been chosen allowed 
            to create a cluster while the word also has a suffix which could be 'transformed' into a cluster. This second wave will make it possible 
            to retrieve all those which can despite everything be attributed to already formed clusters, leaving in the 'None' cluster as few elements 
            as possible, so that the analyst can prioritize his investigation time to the real assets isolated in terms of nomenclature.
        """

        self.clusters = {None: []}

        def get_best_key(s):
            prefixes = summary[s]["prefixes"]
            if len(prefixes) != 0:
                return min(prefixes, key=lambda k: prefixes[k])

            suffixes = summary[s]["suffixes"]
            if len(suffixes) != 0:
                return min(suffixes, key=lambda k: suffixes[k])

            insiders = summary[s]["insiders"]
            if len(insiders) != 0:
                return min(insiders, key=lambda k: insiders[k])

            return None

        original_to_lowercase_dictionary = {s: s.lower() for s in self.strings}
        remainings = [e for e in original_to_lowercase_dictionary.values()]
        potential_clusters = set()

        summary = {}

        for index, e1 in tqdm(list(enumerate(remainings))):
            # longest common matching with all remaining items
            matches = [(i, SequenceMatcher(None, e1, e2).find_longest_match(0, len(e1), 0, len(e2))) for i, e2 in enumerate(remainings) if e2 != e1]
            matches = [t for t in matches if t[1].size >= min(self.min_inside_size, self.min_prefix_suffix_size)]
            if len(matches) > 0:
                matching_summary = pd.DataFrame([(remainings[t[0]], t[1].size, t[1].a, t[1].b, e1[t[1].a : t[1].a + t[1].size]) for t in matches])
                matching_summary.columns = ["string", "size", "start_a", "start_b", "longest_common_substring"]

                matching_summary["is_prefix"] = matching_summary.apply(lambda x: x["start_a"] == 0 and x["start_b"] == 0, axis=1)
                matching_summary["is_suffix"] = matching_summary.apply(lambda x: x["start_a"] + len(x["longest_common_substring"]) == len(e1) and x["start_b"] + len(x["longest_common_substring"]) == len(x["string"]), axis=1)
                matching_summary["is_insider"] = matching_summary.apply(lambda x: not x["is_prefix"] and not x["is_suffix"], axis=1)

                prefixes = {e + "*": len(e) for e in matching_summary[matching_summary["is_prefix"]]["longest_common_substring"] if len(e) >= self.min_prefix_suffix_size}
                suffixes = {"*" + e: len(e) for e in matching_summary[matching_summary["is_suffix"]]["longest_common_substring"] if len(e) >= self.min_prefix_suffix_size}
                insiders = {"*" + e + "*": len(e) for e in matching_summary[matching_summary["is_insider"]]["longest_common_substring"] if len(e) >= self.min_inside_size}

                summary[e1] = {"prefixes": prefixes, "suffixes": suffixes, "insiders": insiders}

                potential_clusters.update(list(prefixes.keys()) + list(suffixes.keys()) + list(insiders.keys()))

            else:
                self.clusters[None].append(e1)

        condition = True
        while condition:
            best_keys = {k: [] for k in potential_clusters}
            for s in summary:
                best_key = get_best_key(s)
                if best_key is None:
                    self.clusters[None].append(s)
                else:
                    best_keys[best_key].append(s)

            temp_condition = False
            for k, l in best_keys.items():
                if len(l) >= self.min_samples:
                    temp_condition = True
                    self.clusters[k] = set(l)
                    potential_clusters.remove(k)
                    for s in l:
                        del summary[s]
            condition = temp_condition

        self.clusters[None].extend(list(summary.keys()))
        self.clusters[None] = set(self.clusters[None])

        to_remove = []
        for string in self.clusters[None]:
            for key in self.clusters:
                if key is not None:
                    key_without_stars = key.replace("*", "")
                    if (
                        (LongestCommonSubstringClustering.is_prefix_cluster(key) and string.startswith(key_without_stars))
                        or (LongestCommonSubstringClustering.is_suffix_cluster(key) and string.endswith(key_without_stars))
                        or (LongestCommonSubstringClustering.is_insider_cluster(key) and key_without_stars in string)
                    ):
                        self.clusters[key].add(string)
                        to_remove.append(string)
                        break
        for string in to_remove:
            self.clusters[None].remove(string)

        # Back to original strings from lowercase
        lowercase_to_original_dictionary = {v: k for k, v in original_to_lowercase_dictionary.items()}
        for cluster_name in self.clusters:
            self.clusters[cluster_name] = set([lowercase_to_original_dictionary[k] for k in self.clusters[cluster_name]])

    @staticmethod
    def is_prefix_cluster(cluster_key: str):
        return not cluster_key.startswith("*") and cluster_key.endswith("*")

    @staticmethod
    def is_suffix_cluster(cluster_key: str):
        return not cluster_key.endswith("*") and cluster_key.startswith("*")

    @staticmethod
    def is_insider_cluster(cluster_key: str):
        return cluster_key.startswith("*") and cluster_key.endswith("*")


class PerDomainAssetClustering:
    """This class implements `LongestCommonSubstringClustering` for each domain of corresponding assets (`Machine` and `Account`).

    Attributes:
        assets (List[Asset]): List of `Asset` objects to cluster.
        domain_clusters(Dict[str, Dict]): Contains the actual computed clusters, classified per domain.
        compare_similar_domains (Callable): Function that compares 2 domain names for possible merging later on.
    """

    def __init__(
        self, 
        assets: List[Asset], 
        compare_similar_domains: Callable = lambda d1, d2: d1.split('.')[0] == d2.split('.')[0]
    ):
        self.assets = assets
        self.domain_clusters: Dict[str, Dict] = {}
        self.compare_similar_domains = compare_similar_domains

    def run(self):
        temp = pd.DataFrame([[asset.name, asset.domain] for asset in self.assets], columns=["name", "domain"])
        temp.replace({None: 'None'}, inplace=True)
        domain_groups = temp.groupby(by=["domain"]).groups
        for domain_name, indices in domain_groups.items(): 
            lcsc = LongestCommonSubstringClustering(list(set(temp.iloc[indices]["name"])))
            lcsc.run()
            domain_name = None if domain_name == 'None' else domain_name
            self.domain_clusters[domain_name] = lcsc.clusters
        self.merge_similar_domains()

    def merge_similar_domains(self):
        remainings = [domain_name for domain_name in self.domain_clusters.keys()]
        while remainings != []:
            domain_name = remainings.pop()
            group = []
            for other_domain_name in remainings:
                try:
                    if self.compare_similar_domains(domain_name, other_domain_name):
                        group.append(other_domain_name)
                        for cluster_name, cluster in self.domain_clusters[other_domain_name].items():
                            if cluster_name in self.domain_clusters[domain_name]:
                                self.domain_clusters[domain_name][cluster_name].update(cluster)
                            else:
                                self.domain_clusters[domain_name][cluster_name] = cluster
                except Exception:
                    pass
            
            if group != []:
                self.domain_clusters[f"{domain_name + ' - ' + ' - '.join(group)}"] = self.domain_clusters.pop(domain_name)
                
                for other_domain_name in group:
                    remainings.remove(other_domain_name)
                    del self.domain_clusters[other_domain_name]

    def plot_clusters(self, firsts_n: Optional[int] = None):
        sorted_clusters = sorted(self.domain_clusters.items(), key=lambda item: len([username for clusters in item[1].values() for username in clusters]), reverse=True)
        to_display = sorted_clusters[:firsts_n] if firsts_n is not None else sorted_clusters
        for domainname, clusters in sorted_clusters:
            print(domainname)
            fig = StringClustering.plot_clusters_static(clusters)
            display(fig)
            print()

    def get_domains_summary(self):
        return pd.DataFrame(
            [[domain, len(clusters), len([name for cluster in clusters.values() for name in cluster])] for domain, clusters in sorted(self.domain_clusters.items(), key=lambda item: len([username for clusters in item[1].values() for username in clusters]), reverse=True)],
            columns=["domain", "nb_clusters", "total_nb_assets"],
        )
