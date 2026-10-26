
import json
from pathlib import Path

file = Path(
    "data/boundary_candidates/complete_road_sources/"
    "vermont_avenue_complete_clean.geojson"
)

with open(file, encoding="utf-8") as f:
    data = json.load(f)

for i, feature in enumerate(data.get("features", []), start=1):
    props = feature.get("properties", {})
    geom = feature.get("geometry", {})

    coords = geom.get("coordinates", [])
    points = []

    def collect(obj):
        if isinstance(obj, list):
            if (
                len(obj) >= 2
                and isinstance(obj[0], (int, float))
                and isinstance(obj[1], (int, float))
            ):
                points.append((obj[0], obj[1]))
            else:
                for item in obj:
                    collect(item)

    collect(coords)

    if points:
        lons = [p[0] for p in points]
        lats = [p[1] for p in points]

        print(
            f"{i:03} | "
            f"OBJECTID={props.get('OBJECTID')} | "
            f"{props.get('STNAME')} {props.get('STSFX')} | "
            f"ADRF={props.get('ADRF')} ADRT={props.get('ADRT')} | "
            f"lon={min(lons):.6f}..{max(lons):.6f} | "
            f"lat={min(lats):.6f}..{max(lats):.6f}"
        )

print("\nInspection complete. No files modified.")

