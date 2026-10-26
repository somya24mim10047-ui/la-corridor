
import pandas as pd
from clustering import run_dbscan

df = pd.read_csv("western_avenue_businesses.csv")

# Run DBSCAN on all business records
all_results = run_dbscan(df.copy(), eps=40, min_samples=4)

# Keep one record per exact coordinate pair
unique_df = df.drop_duplicates(
    subset=["longitude", "latitude"]
).copy()

# Run DBSCAN on unique coordinate pairs
unique_results = run_dbscan(
    unique_df.copy(), eps=40, min_samples=4
)

def report(name, result):
    labels = result["cluster"]
    clusters = labels[labels != -1].nunique()
    noise = (labels == -1).sum()

    print(f"\n{name}")
    print("Records:", len(result))
    print("Clusters:", clusters)
    print("Noise records:", noise)
    print("Cluster sizes:")
    print(labels.value_counts().sort_index().to_string())

report("ALL BUSINESS RECORDS", all_results)
report("UNIQUE COORDINATE PAIRS", unique_results)

unique_results.to_csv(
    "western_avenue_unique_location_clusters.csv",
    index=False
)

print("\nSaved: western_avenue_unique_location_clusters.csv")
