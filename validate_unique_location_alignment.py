
import pandas as pd

# Load unique-location clustering results
df = pd.read_csv("western_avenue_unique_location_clusters.csv")

# Load the previously calculated business-to-road distances
all_df = pd.read_csv("western_avenue_cluster_road_distances.csv")

# Match unique coordinate pairs to their road distances
road_distances = all_df[
    ["longitude", "latitude", "road_distance_m"]
].drop_duplicates(subset=["longitude", "latitude"])

df = df.merge(
    road_distances,
    on=["longitude", "latitude"],
    how="left",
    validate="one_to_one"
)

print("Unique locations:", len(df))
print("Locations with missing road distance:", df["road_distance_m"].isna().sum())

print("\n=== Unique Locations by Cluster ===")
summary = df.groupby("cluster").agg(
    locations=("cluster", "size"),
    median_road_distance_m=("road_distance_m", "median"),
    mean_road_distance_m=("road_distance_m", "mean"),
    within_25m=("road_distance_m", lambda x: (x <= 25).sum()),
    within_50m=("road_distance_m", lambda x: (x <= 50).sum())
).round(2)

print(summary.to_string())

print("\n=== Overall Unique-Location Alignment ===")
print("Median distance (m):", round(df["road_distance_m"].median(), 2))
print("Within 25 m:", int((df["road_distance_m"] <= 25).sum()))
print("Within 50 m:", int((df["road_distance_m"] <= 50).sum()))

df.to_csv("western_avenue_unique_location_alignment.csv", index=False)
print("\nSaved: western_avenue_unique_location_alignment.csv")
