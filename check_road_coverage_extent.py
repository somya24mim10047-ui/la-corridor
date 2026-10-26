
from pathlib import Path

import geopandas as gpd
import pandas as pd

BASE = Path("data/final_corridor_boundaries/selection_candidates")
ROADS = Path("data/boundary_candidates/complete_road_sources")

checks = [
    (
        "olympic_boulevard",
        "olympic_boulevard_excluded_business_review.csv",
        "olympic_boulevard_complete_clean.geojson",
    ),
    (
        "wilshire_boulevard",
        "wilshire_boulevard_excluded_business_review.csv",
        "wilshire_boulevard_complete_clean.geojson",
    ),
]

for corridor, review_file, road_file in checks:
    print(f"\n{'=' * 65}")
    print(corridor.upper())
    print("=" * 65)

    businesses = pd.read_csv(BASE / review_file)
    roads = gpd.read_file(ROADS / road_file)

    if roads.crs is None:
        roads = roads.set_crs("EPSG:4326")

    roads = roads.to_crs("EPSG:32611")

    points = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(
            businesses["longitude"],
            businesses["latitude"],
        ),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    print("Road features:", len(roads))
    print("Road geometry types:", roads.geom_type.value_counts().to_dict())
    print("Road bounds (metres):", roads.total_bounds)

    road_union = roads.geometry.union_all()

    points["distance_to_road_m"] = points.geometry.distance(road_union)

    print("\nExcluded businesses nearest to road:")
    cols = ["business_name", "street_address", "distance_to_road_m"]
    print(
        points[cols]
        .sort_values("distance_to_road_m")
        .head(5)
        .to_string(index=False)
    )

    print("\nRoad distance distribution:")
    print(
        points["distance_to_road_m"]
        .describe(percentiles=[0.25, 0.5, 0.75, 0.9])
        .round(2)
        .to_string()
    )

