import pandas as pd
from clustering import run_dbscan, cluster_summary

df = pd.read_csv("western_avenue_businesses.csv")

result = run_dbscan(
    df,
    eps=100,
    min_samples=4
)

print("\nCluster labels:")
print(result["cluster"].value_counts().sort_index())

print("\nCluster summary:")
print(cluster_summary(result).to_string(index=False))

result.to_csv(
    "western_avenue_clustered.csv",
    index=False
)

print("\nSaved western_avenue_clustered.csv")