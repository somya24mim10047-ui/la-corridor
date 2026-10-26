
import json
import pandas as pd
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.ops import transform
from pyproj import Transformer

root = Path(".")
road_folder = root / "data/boundary_candidates/complete_road_sources"

project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

targets = [
    ("SJ INVESTMENT 2020 LLC", 34.0487, -118.3362),
    ("LOS ANGELES HIGH SCHOOL ALUMNI ASSOCIATION", 34.0551, -118.3328),
    ("ELENA L GARCIA", 34.0761, -118.3031),
    ("WOORI MEDIA GROUP LLC", 34.0602, -118.2874),
]

roads = []

for file in road_folder.glob("*_complete_clean.geojson"):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    for feature in data.get("features", []):
        geometry = feature.get("geometry")
        if not geometry:
            continue

        props = feature.get("properties", {})
        line = transform(project, shape(geometry))

        roads.append({
            "name": f"{props.get('STNAME', '')} {props.get('STSFX', '')}".strip(),
            "from": props.get("ADRF"),
            "to": props.get("ADRT"),
            "objectid": props.get("OBJECTID"),
            "geometry": line,
        })

for name, lat, lon in targets:
    point = transform(project, Point(lon, lat))
    results = sorted(
        ((point.distance(r["geometry"]), r) for r in roads),
        key=lambda x: x[0]
    )

    print(f"\n{'=' * 65}\n{name}")
    print(f"Coordinates: {lat}, {lon}")
    print("Nearest official road segments:")

    for distance, road in results[:10]:
        print(
            f"{distance:8.1f} m | {road['name']:<22} | "
            f"range {road['from']}-{road['to']} | "
            f"OBJECTID={road['objectid']}"
        )

print("\nNearby-street check complete. No files modified.")
