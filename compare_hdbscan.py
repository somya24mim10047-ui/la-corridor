
import pandas as pd
import numpy as np
import hdbscan

from sklearn.cluster import DBSCAN
from pyproj import Transformer

# Convert longitude/latitude to coordinates in metres
transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32611",
    always_xy=True
)


def compare_methods(file_path, label):
    df = pd.read_csv(file_path)

    # Use unique geographic locations for clustering
    coords = df[["longitude", "latitude"]].dropna()
    x, y = transformer.transform(
        coords["longitude"].to_numpy(),
        coords["latitude"].to_numpy()
    )
    points = np.column_stack((x, y))

    # DBSCAN: current baseline
    dbscan_labels = DBSCAN(
        eps=40,
        min_samples=4
    ).fit_predict(points)

    # HDBSCAN: variable-density clustering
    hdbscan_labels = hdbscan.HDBSCAN(
        min_cluster_size=4,
        min_samples=4,
        metric="euclidean"
    ).fit_predict(points)

    def summarize(labels, method):
        cluster_count = len(set(labels) - {-1})
        noise_count = int(np.sum(labels == -1))

        return {
            "dataset": label,
            "method": method,
            "locations": len(labels),
            "clusters": cluster_count,
            "noise_locations": noise_count
        }

    return [
        summarize(dbscan_labels, "DBSCAN (40m)"),
        summarize(hdbscan_labels, "HDBSCAN")
    ]


results = []

results.extend(compare_methods(
    "western_avenue_businesses.csv",
    "All business records"
))

results.extend(compare_methods(
    "western_avenue_unique_location_clusters.csv",
    "Unique coordinate pairs"
))

report = pd.DataFrame(results)

print("\n=== DBSCAN vs HDBSCAN ===")
print(report.to_string(index=False))

report.to_csv(
    "western_avenue_hdbscan_comparison.csv",
    index=False
)

print("\nSaved: western_avenue_hdbscan_comparison.csv")
