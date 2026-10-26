import json
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.ops import transform
from pyproj import Transformer

folder = Path("data/boundary_candidates/complete_road_sources")
project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

for file in sorted(folder.glob("*_complete_clean.geojson")):
    data = json.loads(file.read_text(encoding="utf-8"))
    lines = []

    for feature in data.get("features", []):
        geom = feature.get("geometry")
        if geom:
            projected = transform(project, shape(geom))
            if projected.geom_type == "LineString":
                lines.append(projected)
            elif projected.geom_type == "MultiLineString":
                lines.extend(projected.geoms)

    endpoints = []
    for i, line in enumerate(lines):
        coords = list(line.coords)
        endpoints.append((i, "start", Point(coords[0])))
        endpoints.append((i, "end", Point(coords[-1])))

    results = []
    for line_id, end_name, point in endpoints:
        nearest = min(
            (point.distance(other), j)
            for j, other in enumerate(lines)
            if j != line_id
        ) if len(lines) > 1 else (float("inf"), None)

        results.append((nearest[0], line_id, end_name, nearest[1]))

    flagged = [r for r in results if r[0] > 25]

    print(f"\n{file.name}")
    print(f"Road lines: {len(lines)}")
    print(f"Endpoints checked: {len(results)}")
    print(f"Endpoints more than 25 m from another road line: {len(flagged)}")

    for distance, line_id, end_name, nearest_id in sorted(flagged, reverse=True)[:15]:
        print(
            f"  Line {line_id} {end_name}: "
            f"nearest other line = {distance:.2f} m (line {nearest_id})"
        )

print("\nEndpoint connectivity check complete. Source files unchanged.")
