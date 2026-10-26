
import json
import pandas as pd
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.ops import transform, unary_union
from pyproj import Transformer

root = Path(".")
road_file = root / "data/boundary_candidates/complete_road_sources/olympic_boulevard_complete_clean.geojson"

business_file = root / "data/corridors/olympic_boulevard_businesses.csv"

project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

with open(road_file, encoding="utf-8") as f:
    road_data = json.load(f)

roads = [
    transform(project, shape(feature["geometry"]))
    for feature in road_data["features"]
    if feature.get("geometry")
]

road_union = unary_union(roads)
businesses = pd.read_csv(business_file)

targets = [
    "SJ INVESTMENT 2020 LLC",
    "LOS ANGELES HIGH SCHOOL ALUMNI ASSOCIATION",
]

for name in targets:
    matches = businesses[
        businesses["business_name"].astype(str).str.contains(
            name, case=False, regex=False, na=False
        )
    ]

    print(f"\n{name}: {len(matches)} matching record(s)")

    for _, row in matches.iterrows():
        point = transform(
            project,
            Point(float(row["longitude"]), float(row["latitude"]))
        )
        print("Address:", row["street_address"])
        print("Coordinates:", row["latitude"], row["longitude"])
        print("Distance to Olympic geometry:", round(point.distance(road_union), 2), "m")

print("\nCheck complete. No files modified.")
