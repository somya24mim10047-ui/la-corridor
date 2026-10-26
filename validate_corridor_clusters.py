
import json
import pandas as pd
from pathlib import Path
from shapely.geometry import shape, Point
from pyproj import Transformer

# ---------- FILES ----------
BUSINESS_FILE = "western_avenue_businesses.csv"
CLUSTER_FILE = "western_avenue_unique_location_clusters.csv"
ROAD_FILE = "western_avenue_centerline.geojson"

# LA uses UTM Zone 11N for distance calculations
transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
)

# ---------- LOAD DATA ----------
businesses = pd.read_csv(BUSINESS_FILE)
clusters = pd.read_csv(CLUSTER_FILE)

# Support either the earlier 'cluster' column or the new pipeline labels
cluster_columns = [
    c for c in ["cluster", "dbscan_cluster", "hdbscan_cluster"]
    if c in clusters.columns
]

if not cluster_columns:
    raise ValueError(
        "No cluster label found. Check the columns in "
        + CLUSTER_FILE
    )

# Keep one row per exact coordinate pair
clusters = clusters.drop_duplicates(
    subset=["longitude", "latitude"]
).copy()

# ---------- LOAD AND PROJECT ROAD ----------
with open(ROAD_FILE, "r", encoding="utf-8") as file:
    road_data = json.load(file)

features = road_data.get("features", [])
if road_data.get("type") == "Feature":
    features = [road_data]

road_geometries = [
    shape(feature["geometry"])
    for feature in features
    if feature.get("geometry")
]

if not road_geometries:
    raise ValueError("No road geometry found in the GeoJSON file.")

from shapely.ops import transform as transform_geometry

projected_roads = [
    transform_geometry(transformer.transform, road)
    for road in road_geometries
]

# ---------- CALCULATE DISTANCE TO ROAD ----------
def road_distance(row):
    x, y = transformer.transform(
        row["longitude"], row["latitude"]
    )
    point = Point(x, y)
    return min(point.distance(road) for road in projected_roads)

clusters["road_distance_m"] = clusters.apply(
    road_distance, axis=1
)

# ---------- CLUSTER VALIDATION ----------
summary_rows = []

for method in cluster_columns:
    for cluster_id, group in clusters.groupby(
        method, dropna=False
    ):
        summary_rows.append({
            "method": method,
            "cluster": cluster_id,
            "locations": len(group),
            "median_road_distance_m": round(
                group["road_distance_m"].median(), 2
            ),
            "mean_road_distance_m": round(
                group["road_distance_m"].mean(), 2
            ),
            "within_25m": int(
                (group["road_distance_m"] <= 25).sum()
            ),
            "within_50m": int(
                (group["road_distance_m"] <= 50).sum()
            )
        })

summary = pd.DataFrame(summary_rows)
summary.to_csv(
    "western_avenue_cluster_validation.csv", index=False
)

# ---------- BUSINESS COMPOSITION ----------
# Join cluster labels to all business records by coordinates
label_columns = ["longitude", "latitude"] + cluster_columns
label_map = clusters[label_columns].drop_duplicates(
    subset=["longitude", "latitude"]
)

joined = businesses.merge(
    label_map,
    on=["longitude", "latitude"],
    how="left"
)

for method in cluster_columns:
    category_column = "primary_naics_description"

    if category_column not in joined.columns:
        print("Business category column not found.")
        break

    composition = (
        joined.groupby([method, category_column], dropna=False)
        .size()
        .reset_index(name="business_count")
        .sort_values(
            [method, "business_count"],
            ascending=[True, False]
        )
    )

    composition.to_csv(
        f"western_avenue_{method}_business_composition.csv",
        index=False
    )

print("\n=== CLUSTER VALIDATION REPORT ===")
print(summary.to_string(index=False))

print("\nUnique locations:", len(clusters))
print(
    "Locations within 25m of Western Avenue:",
    int((clusters["road_distance_m"] <= 25).sum())
)
print(
    "Locations within 50m of Western Avenue:",
    int((clusters["road_distance_m"] <= 50).sum())
)

print("\nSaved:")
print("- western_avenue_cluster_validation.csv")
for method in cluster_columns:
    print(f"- western_avenue_{method}_business_composition.csv")
