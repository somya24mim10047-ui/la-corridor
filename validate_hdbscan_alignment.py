
import pandas as pd

# Load unique locations
df = pd.read_csv("western_avenue_unique_location_clusters.csv")

# Load business-level road distances
distances = pd.read_csv("western_avenue_cluster_road_distances.csv")

# Keep one road distance for each exact coordinate pair
distances = distances.drop_duplicates(
    subset=["longitude", "latitude"]
)

# Merge road distances onto unique locations
df = df.drop(columns=["cluster"], errors="ignore")

df = df.merge(
    distances[["longitude", "latitude", "road_distance_m"]],
    on=["longitude", "latitude"],
    how="left"
)

# Load HDBSCAN results by rerunning the same settings
import numpy as np
import hdbscan
from pyproj import Transformer

transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
)

x, y = transformer.transform(
    df["longitude"].to_numpy(),
    df["latitude"].to_numpy()
)
points = np.column_stack((x, y))

df["hdbscan_cluster"] = hdbscan.HDBSCAN(
    min_cluster_size=4,
    min_samples=4,
    metric="euclidean"
).fit_predict(points)

# Summarize each cluster's road alignment
summary = df.groupby("hdbscan_cluster").agg(
    locations=("longitude", "size"),
    median_road_distance_m=("road_distance_m", "median"),
    mean_road_distance_m=("road_distance_m", "mean"),
    within_25m=("road_distance_m", lambda s: (s <= 25).sum()),
    within_50m=("road_distance_m", lambda s: (s <= 50).sum())
).round(2)

print("\n=== HDBSCAN Road Alignment ===")
print(summary.to_string())

print("\nOverall median road distance:",
      round(df["road_distance_m"].median(), 2), "m")
print("Locations within 25 m:",
      int((df["road_distance_m"] <= 25).sum()))
print("Locations within 50 m:",
      int((df["road_distance_m"] <= 50).sum()))

df.to_csv("western_avenue_hdbscan_alignment.csv", index=False)
summary.to_csv("western_avenue_hdbscan_alignment_summary.csv")

print("\nAlignment reports saved.")
