
import json
from pathlib import Path
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

folder = Path("data/boundary_candidates/complete_road_sources")

project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

for file in sorted(folder.glob("*_complete_clean.geojson")):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    segments = []

    for feature in data.get("features", []):
        geometry = feature.get("geometry")
        if not geometry:
            continue

        props = feature.get("properties", {})
        line = transform(project, shape(geometry))

        if line.geom_type == "LineString":
            segments.append((props, line))
        elif line.geom_type == "MultiLineString":
            segments.extend((props, part) for part in line.geoms)

    print(f"\n{'=' * 65}\n{file.name}")
    print(f"Segments: {len(segments)}")

    nearest_distances = []

    for i, (props_a, line_a) in enumerate(segments):
        best = None

        for j, (props_b, line_b) in enumerate(segments):
            if i == j:
                continue

            distance = line_a.distance(line_b)

            if best is None or distance < best[0]:
                best = (distance, props_b, j)

        if best:
            nearest_distances.append(best[0])

            if best[0] > 100:
                print(
                    f"Potential isolated segment: "
                    f"OBJECTID={props_a.get('OBJECTID')}, "
                    f"nearest OBJECTID={best[1].get('OBJECTID')}, "
                    f"distance={best[0]:.1f} m"
                )

    if nearest_distances:
        print(
            f"Nearest-neighbor distances: "
            f"max={max(nearest_distances):.1f} m, "
            f"over 25 m={sum(d > 25 for d in nearest_distances)}, "
            f"over 100 m={sum(d > 100 for d in nearest_distances)}"
        )

print("\nNearest-segment check complete. No files modified.")
