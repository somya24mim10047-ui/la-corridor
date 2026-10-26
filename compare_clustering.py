
import pandas as pd
from clustering import run_dbscan

df = pd.read_csv("western_avenue_businesses.csv")

settings = [
    (25, 4),
    (40, 4),
    (60, 4),
    (80, 4),
    (100, 4),
]

for eps, min_samples in settings:
    result = run_dbscan(
        df,
        eps=eps,
        min_samples=min_samples
    )

    labels = result["cluster"]
    real_clusters = set(labels) - {-1}
    noise_count = (labels == -1).sum()

    print(f"\neps = {eps} metres")
    print("Number of clusters:", len(real_clusters))
    print("Noise businesses:", noise_count)
    print("Cluster sizes:")
    print(labels[labels != -1].value_counts().sort_values(
        ascending=False
    ).to_list())
