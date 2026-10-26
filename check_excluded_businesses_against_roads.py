
from pathlib import Path

import geopandas as gpd
import pandas as pd

BASE = Path("data/final_corridor_boundaries/selection_candidates")
ROADS = Path("data/boundary_candidates/complete_road_sources")

checks = [
    (
        "olympic_boulevard",
        "olympic_boulevard_excluded_business_review.csv",
        "olympic_boulevard_50m_candidate.geojson",
        "olympic_boulevard_complete_clean.geojson",
    ),
    (
        "wilshire_boulevard",
        "wilshire_boulevard_excluded_business_review.csv",
        "wilshire_boulevard_100m_candidate.geojson",
        "wilshire_boulevard_complete_clean.geojson",
    ),
]

for corridor, review_file, candidate_file, road_file in checks:
    print(f"\n{'=' * 65}")
    print(f"{corridor.upper()}")
    print("=" * 65)

    df = pd.read_csv(BASE / review_file)

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    roads = gpd.read_file(ROADS / road_file)
    if roads.crs is None:
        roads = roads.set_crs("EPSG:4326")
    roads = roads.to_crs("EPSG:32611")

    candidate = gpd.read_file(BASE / candidate_file)
    if candidate.crs is None:
        candidate = candidate.set_crs("EPSG:4326")
    candidate = candidate.to_crs("EPSG:32611")

    road_union = roads.geometry.union_all()
    boundary_union = candidate.geometry.union_all()

    points["actual_road_distance_m"] = points.geometry.distance(
        road_union
    )
    points["inside_candidate"] = points.geometry.apply(
        boundary_union.covers
    )

    print("Excluded businesses checked:", len(points))
    print(
        "Within 25 m of road:",
        int((points["actual_road_distance_m"] <= 25).sum()),
    )
    print(
        "Within 50 m of road:",
        int((points["actual_road_distance_m"] <= 50).sum()),
    )
    print(
        "More than 100 m from road:",
        int((points["actual_road_distance_m"] > 100).sum()),
    )

    print("\nClosest excluded businesses to the actual road:")
    cols = [
        "business_name",
        "street_address",
        "actual_road_distance_m",
    ]
    print(
        points[cols]
        .sort_values("actual_road_distance_m")
        .head(15)
        .to_string(index=False)
    )

    output = BASE / f"{corridor}_road_distance_check.csv"
    points.drop(columns="geometry").to_csv(output, index=False)
    print("\nSaved:", output)
