
import json
import math
from pathlib import Path
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

folder = Path("data/boundary_candidates/complete_road_sources")

# Convert longitude/latitude to metres for distance calculations.
project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

for file in sorted(folder.glob("*_complete_clean.geojson")):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    lines = []

    for feature in data.get("features", []):
        geometry = feature.get("geometry")
        if not geometry:
            continue

        line = transform(project, shape(geometry))
        if line.geom_type == "LineString":
            lines.append(line)
        elif line.geom_type == "MultiLineString":
            lines.extend(list(line.geoms))

    gaps = []

    for i, line_a in enumerate(lines):
        for line_b in lines[i + 1:]:
            # Ignore overlapping or connected segments.
            distance = line_a.distance(line_b)
            if distance > 0.5:
                gaps.append(distance)

    print(f"\n{file.name}")
    print(f"Road segments: {len(lines)}")

    if not gaps:
        print("No gaps greater than 0.5 m found.")
    else:
        print(f"Smallest separated-segment distance: {min(gaps):.2f} m")
        print(f"Largest separated-segment distance: {max(gaps):.2f} m")
        print(f"Pairs separated by more than 25 m: {sum(g > 25 for g in gaps)}")
        print(f"Pairs separated by more than 100 m: {sum(g > 100 for g in gaps)}")

print("\nGeometry gap check complete. No files modified.")
