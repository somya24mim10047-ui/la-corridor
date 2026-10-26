
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np

BASE = Path(__file__).parent
CLUSTER_DIR = (
    BASE / "data" / "clustered" / "provisional_boundary_review"
)
ROAD_DIR = (
    BASE / "data" / "boundary_candidates" / "complete_road_sources"
)
OUT_DIR = CLUSTER_DIR / "road_alignment_review"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = [
    "larchmont_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "wilshire_boulevard",
]

rows = []

for corridor in CORRIDORS:
    business_file = CLUSTER_DIR / f"{corridor}_provisional_clusters.csv"
    road_file = ROAD_DIR / f"{corridor}_complete_clean.geojson"

    if not business_file.exists():
        print(f"SKIP: Missing business file: {business_file.name}")
        continue

    if not road_file.exists():
        print(f"SKIP: Missing road file: {road_file.name}")
        continue

    df = pd.read_csv(business_file)
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    roads = gpd.read_file(road_file)

    if roads.crs is None:
        print(f"SKIP: Road CRS missing: {road_file.name}")
        continue

    # Convert coordinates and road geometry to metres (UTM zone 11N).
    businesses = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    roads = roads.to_crs("EPSG:32611")
    road_union = roads.geometry.union_all()

    # Measure each business's straight-line distance to the road geometry.
    businesses["road_distance_m"] = (
        businesses.geometry.distance(road_union)
    )

    # Provisional distance bands; these do not decide final inclusion.
    businesses["within_50m"] = businesses["road_distance_m"] <= 50
    businesses["within_100m"] = businesses["road_distance_m"] <= 100
    businesses["within_125m"] = businesses["road_distance_m"] <= 125
    businesses["within_150m"] = businesses["road_distance_m"] <= 150

    business_output = OUT_DIR / f"{corridor}_road_distances.csv"
    businesses.drop(columns="geometry").to_csv(business_output, index=False)

    for cluster_id, group in businesses.groupby("cluster_id"):
        distances = group["road_distance_m"]

        rows.append({
            "corridor": corridor,
            "cluster_id": int(cluster_id),
            "business_records": len(group),
            "median_road_distance_m": round(distances.median(), 2),
            "mean_road_distance_m": round(distances.mean(), 2),
            "max_road_distance_m": round(distances.max(), 2),
            "within_50m": int(group["within_50m"].sum()),
            "within_100m": int(group["within_100m"].sum()),
            "within_125m": int(group["within_125m"].sum()),
            "within_150m": int(group["within_150m"].sum()),
        })

    print(f"\n{corridor}")
    print(f"Businesses checked: {len(businesses)}")
    print(f"Within 50 m: {businesses['within_50m'].sum()}")
    print(f"Within 100 m: {businesses['within_100m'].sum()}")
    print(f"Saved: {business_output.name}")

summary = pd.DataFrame(rows)
summary_file = OUT_DIR / "cluster_road_alignment_summary.csv"
summary.to_csv(summary_file, index=False)

print("\n=== CLUSTER-TO-ROAD ALIGNMENT SUMMARY ===")
if not summary.empty:
    print(summary.to_string(index=False))
print(f"\nSaved: {summary_file}")
print("Original datasets and clustering outputs were not modified.")
