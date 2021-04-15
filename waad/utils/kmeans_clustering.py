"""This module implements some facilities to run a Kmeans clustering without knowing the number of desired clusters."""


import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from typing import List


class KmeansClustering:
    def __init__(self, data: np.ndarray):
        self.X = data.reshape(-1, 1)
        self.k_values: List[int] = []
        self.sil_score: List[float] = []
        self.best_k = None
        self.kmeans = None

    def run(self):
        k_max = min(20, self.X.shape[0])

        if k_max > 2:
            self.sil_score = []
            self.k_values = [i for i in range(2, k_max)]
            for k in self.k_values:
                kmeans = KMeans(n_clusters=k).fit(self.X)
                self.sil_score.append(silhouette_score(self.X, kmeans.labels_, metric="euclidean"))

            self.best_k = self.k_values[np.argmax(self.sil_score)]
            self.kmeans = KMeans(n_clusters=self.best_k).fit(self.X)

    def plot_silhouette_score(self):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(self.k_values, self.sil_score, marker="o")
        ax.vlines(self.best_k, *ax.get_ylim(), colors="r")
        ax.set_xlabel("Number of clusters")
        ax.set_ylabel("Average Silhouette score")
        return fig

    def plot_clusters(self):
        # Visualize clusters
        colors = plt.cm.get_cmap("hsv", len(self.kmeans.cluster_centers_) + 1)
        fig, ax = plt.subplots()
        for n, y in enumerate(self.X[:, 0]):
            ax.plot(1, y, marker="x", color=colors(self.kmeans.labels_[n]), ms=10)
        ax.set_ylabel("Duration in seconds")
        ax.set_title("Kmeans cluster visualization")
        return fig
