
import pandas as pd
import numpy as np
import hdbscan

from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from pyproj import Transformer

# Use unique geographic locations
df = pd.read_csv("western_avenue_unique_location_clusters.csv")
df = df.dropna(subset=["longitude", "latitude"]).copy()
df = df.drop_duplicates(subset=["longitude", "latitude"])

# Convert coordinates to metres
transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
)

x, y = transformer.transform(
    df["longitude"].to_numpy(),
    df["latitude"].to_numpy()
)
points = np.column_stack((x, y))


def evaluate(labels):
    valid = labels != -1
    kept_labels = labels[valid]
    cluster_ids = set(kept_labels)
    cluster_count = len(cluster_ids)
    noise_count = int((labels == -1).sum())

    score = np.nan
    if (
        cluster_count >= 2
        and len(kept_labels) > cluster_count
    ):
        score = silhouette_score(points[valid], kept_labels)

    return {
        "clusters": cluster_count,
        "noise": noise_count,
        "largest_cluster": max(
            [int((labels == c).sum()) for c in cluster_ids],
            default=0
        ),
        "silhouette": round(score, 3) if np.isfinite(score) else None
    }


results = []

# Test several DBSCAN distances
for eps in [25, 30, 35, 40, 45, 50]:
    labels = DBSCAN(
        eps=eps,
        min_samples=4
    ).fit_predict(points)

    results.append({
        "method": "DBSCAN",
        "setting": f"eps={eps}m, min_samples=4",
        **evaluate(labels)
    })

# Test several HDBSCAN settings
for min_size in [4, 5, 6]:
    for min_samples in [2, 4]:
        labels = hdbscan.HDBSCAN(
            min_cluster_size=min_size,
            min_samples=min_samples,
            metric="euclidean"
        ).fit_predict(points)

        results.append({
            "method": "HDBSCAN",
            "setting": (
                f"min_cluster_size={min_size}, "
                f"min_samples={min_samples}"
            ),
            **evaluate(labels)
        })

report = pd.DataFrame(results)

print("\n=== CLUSTERING STABILITY TEST ===")
print(report.to_string(index=False))

report.to_csv(
    "western_avenue_clustering_stability.csv",
    index=False
)

print("\nSaved: western_avenue_clustering_stability.csv")
