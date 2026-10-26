
from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "data" / "boundary_candidates" / "outside_businesses"
ROAD_DIR = ROOT / "data" / "corridors"
CRS_METRIC = "EPSG:32611"

corridors = ["wilshire_boulevard", "olympic_boulevard"]

for corridor in corridors:
    outside_file = BASE / f"{corridor}_outside_100m.csv"
    road_file = ROAD_DIR / f"{corridor}_road_segments_clean.geojson"

    if not outside_file.exists() or not road_file.exists():
        print(f"Missing input file for {corridor}")
        continue

    df = pd.read_csv(outside_file)
    roads = gpd.read_file(road_file).to_crs(CRS_METRIC)

    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df = df.dropna(subset=["longitude", "latitude"]).copy()

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    ).to_crs(CRS_METRIC)

    road_union = roads.geometry.union_all()

    # Actual shortest distance from each business point to a road line
    points["distance_to_road_m"] = points.geometry.distance(road_union)
    points["distance_band"] = pd.cut(
        points["distance_to_road_m"],
        bins=[-1, 25, 50, 100, 150, 250, float("inf")],
        labels=["0-25m", "25-50m", "50-100m", "100-150m",
                "150-250m", "250m+"],
    )

    output = BASE / f"{corridor}_outside_100m_road_audit.csv"
    points.drop(columns="geometry").to_csv(output, index=False)

    print(f"\n=== {corridor.upper()} ===")
    print("Excluded business records:", len(points))
    print("\nDistance to actual road geometry:")
    print(points["distance_band"].value_counts(sort=False).to_string())
    print("\nClosest 10 excluded businesses:")
    print(
        points.sort_values("distance_to_road_m")[
            ["business_name", "street_address", "distance_to_road_m"]
        ].head(10).to_string(index=False)
    )
    print(f"\nSaved: {output}")

print("\nAudit complete.")
