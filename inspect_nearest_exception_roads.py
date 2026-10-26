
from pathlib import Path
import pandas as pd
import geopandas as gpd

BASE = Path(__file__).resolve().parent
ROAD_DIR = BASE / "data" / "boundary_candidates" / "complete_road_sources"
AUDIT_DIR = BASE / "data" / "boundary_candidates" / "all_corridor_audit"

FILES = {
    "wilshire_boulevard": "wilshire_boulevard_outside_150m.csv",
    "olympic_boulevard": "olympic_boulevard_outside_100m.csv",
    "vermont_avenue": "vermont_avenue_outside_100m.csv",
}

for corridor, csv_name in FILES.items():
    print(f"\n{'=' * 18} {corridor.upper()} {'=' * 18}")

    road_file = ROAD_DIR / f"{corridor}_complete_clean.geojson"
    exception_file = AUDIT_DIR / csv_name

    roads = gpd.read_file(road_file).to_crs("EPSG:32611")
    exceptions = pd.read_csv(exception_file)

    points = gpd.GeoDataFrame(
        exceptions,
        geometry=gpd.points_from_xy(
            exceptions["longitude"], exceptions["latitude"]
        ),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    for _, point in points.iterrows():
        distances = roads.geometry.distance(point.geometry)
        nearest_index = distances.idxmin()
        nearest = roads.loc[nearest_index]

        print(f"\nBusiness: {point['business_name']}")
        print(f"Address: {point['street_address']}")
        print(f"Recorded road distance: {point['road_distance_m']:.2f} m")
        print(f"Nearest retrieved segment distance: {distances.loc[nearest_index]:.2f} m")

        for field in ["STNAME", "STSFX", "ADRF", "ADRT", "OBJECTID"]:
            if field in nearest.index:
                print(f"{field}: {nearest[field]}")

print("\nInspection complete. No files were modified.")
