
import pandas as pd

# Load the updated clustering results
df = pd.read_csv("western_avenue_clustered.csv")

# Summarize the geographic location of each cluster
summary = df.groupby("cluster").agg(
    business_count=("business_name", "count"),
    min_lat=("latitude", "min"),
    max_lat=("latitude", "max"),
    min_lon=("longitude", "min"),
    max_lon=("longitude", "max"),
    avg_lat=("latitude", "mean"),
    avg_lon=("longitude", "mean")
).reset_index()

# Calculate approximate north-south and east-west spread
summary["north_south_m"] = (
    (summary["max_lat"] - summary["min_lat"]) * 111000
).round(1)

summary["east_west_m"] = (
    (summary["max_lon"] - summary["min_lon"])
    * 111000
    * 0.83
).round(1)

print("\n=== Geographic Summary of DBSCAN Clusters ===")
print(summary.round(6).to_string(index=False))

summary.to_csv("western_avenue_cluster_summary.csv", index=False)

print("\nSaved: western_avenue_cluster_summary.csv")
