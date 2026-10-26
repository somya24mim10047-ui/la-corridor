
import json
import pandas as pd
from shapely.geometry import shape, Point
from shapely.ops import transform, unary_union
from pyproj import Transformer

# Load clustered businesses
df = pd.read_csv("western_avenue_clustered.csv")

# Load the existing road centerline
with open("western_avenue_centerline.geojson", "r", encoding="utf-8") as f:
    geojson = json.load(f)

# Extract road geometries from GeoJSON
if geojson["type"] == "FeatureCollection":
    geometries = [
        shape(feature["geometry"])
        for feature in geojson["features"]
        if feature.get("geometry")
    ]
elif geojson["type"] == "Feature":
    geometries = [shape(geojson["geometry"])]
else:
    geometries = [shape(geojson)]

if not geometries:
    raise ValueError("No road geometry found in the GeoJSON file.")

# Project coordinates into metres (UTM Zone 11N)
project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

road = unary_union([
    transform(project, geometry) for geometry in geometries
])

# Calculate each business's distance to the road
df["road_distance_m"] = df.apply(
    lambda row: Point(
        *project(row["longitude"], row["latitude"])
    ).distance(road),
    axis=1
)

# Save individual business distances
df.to_csv("western_avenue_cluster_road_distances.csv", index=False)

# Summarize distance by cluster
summary = df.groupby("cluster").agg(
    businesses=("business_name", "size"),
    median_distance_m=("road_distance_m", "median"),
    mean_distance_m=("road_distance_m", "mean"),
    max_distance_m=("road_distance_m", "max"),
    within_25m=("road_distance_m", lambda x: (x <= 25).sum()),
    within_50m=("road_distance_m", lambda x: (x <= 50).sum())
).round(2)

print("\n=== Business-to-Road Distance by Cluster ===")
print(summary.to_string())

print("\n=== Overall Road Alignment ===")
print("Businesses:", len(df))
print("Median distance (m):", round(df["road_distance_m"].median(), 2))
print("Mean distance (m):", round(df["road_distance_m"].mean(), 2))
print("Within 25 m:", int((df["road_distance_m"] <= 25).sum()))
print("Within 50 m:", int((df["road_distance_m"] <= 50).sum()))

print("\nSaved: western_avenue_cluster_road_distances.csv")
