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
        if not geom:
            continue
        projected = transform(project, shape(geom))
        parts = list(projected.geoms) if projected.geom_type == "MultiLineString" else [projected]
        for part in parts:
            if part.geom_type == "LineString":
                lines.append((part, feature.get("properties", {})))

    flagged = []
    for i, (line, props) in enumerate(lines):
        coords = list(line.coords)
        for label, coord in [("start", coords[0]), ("end", coords[-1])]:
            point = Point(coord)
            others = [
                (point.distance(other), j)
                for j, (other, _) in enumerate(lines) if j != i
            ]
            if others:
                distance, nearest_id = min(others)
                if distance > 25:
                    flagged.append((distance, i, label, nearest_id, props))

    if flagged:
        print(f"\n{file.name}")
        for distance, idx, label, nearest_id, props in sorted(flagged, reverse=True):
            print(
                f"  line={idx}, endpoint={label}, distance={distance:.2f} m, "
                f"nearest_line={nearest_id}, OBJECTID={props.get('OBJECTID')}, "
                f"street={props.get('STNAME')} {props.get('STSFX')}, "
                f"ADRF={props.get('ADRF')}, ADRT={props.get('ADRT')}"
            )

print("\nEndpoint review listing complete. No source files modified.")
