import geopandas as gpd
import pandas as pd
from pathlib import Path

ROOT = Path(".")
OUT = ROOT / "data" / "final_corridor_boundaries"
OUT.mkdir(parents=True, exist_ok=True)

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    print(f"\n=== {name.upper()} ===")

    boundary = gpd.read_file(
        OUT / f"{name}_boundary.geojson"
    ).to_crs("EPSG:32611")

    businesses = pd.read_csv(
        ROOT / "data" / "corridors" / f"{name}_businesses.csv"
    )

    points = gpd.GeoDataFrame(
        businesses.copy(),
        geometry=gpd.points_from_xy(
            businesses["longitude"],
            businesses["latitude"]
        ),
        crs="EPSG:4326"
    ).to_crs("EPSG:32611")

    roads = gpd.read_file(
        ROOT / "data" / "boundary_candidates" /
        "complete_road_sources" /
        f"{name}_complete_clean.geojson"
    ).to_crs("EPSG:32611")

    road_geometry = roads.geometry.union_all()
    boundary_geometry = boundary.geometry.union_all()

    points["inside_boundary"] = points.geometry.map(
        boundary_geometry.covers
    )
    points["road_distance_m"] = points.geometry.distance(
        road_geometry
    )

    outside = points.loc[~points["inside_boundary"]].copy()
    outside["longitude"] = outside.geometry.x
    outside["latitude"] = outside.geometry.y

    print("Excluded businesses:", len(outside))
    print("Within 25 m of road:", (outside.road_distance_m <= 25).sum())
    print("Within 50 m of road:", (outside.road_distance_m <= 50).sum())
    print("Within 100 m of road:", (outside.road_distance_m <= 100).sum())

    columns = [
        c for c in [
            "business_name", "street_address",
            "primary_naics_description",
            "longitude", "latitude", "road_distance_m"
        ] if c in outside.columns
    ]

    outside[columns].sort_values("road_distance_m").to_csv(
        OUT / f"{name}_outside_business_diagnostic.csv",
        index=False
    )

    print(
        "Saved:",
        OUT / f"{name}_outside_business_diagnostic.csv"
    )
