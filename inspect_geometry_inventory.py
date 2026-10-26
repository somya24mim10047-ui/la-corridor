import json
from pathlib import Path

root = Path(".")
files = [
    root / "western_avenue_final_boundary.geojson",
    root / "western_avenue_centerline.geojson",
    root / "data/boundary_candidates/complete_road_sources/larchmont_boulevard_complete_clean.geojson",
    root / "data/boundary_candidates/complete_road_sources/olympic_boulevard_complete_clean.geojson",
    root / "data/boundary_candidates/complete_road_sources/vermont_avenue_complete_clean.geojson",
    root / "data/boundary_candidates/complete_road_sources/wilshire_boulevard_complete_clean.geojson",
    root / "data/corridors/larchmont_boulevard_road_segments_clean.geojson",
]

def walk_coords(obj):
    if not isinstance(obj, (list, tuple)):
        return
    if len(obj) >= 2 and all(isinstance(v, (int, float)) for v in obj[:2]):
        yield obj[0], obj[1]
    else:
        for item in obj:
            yield from walk_coords(item)

for path in files:
    print(f"\n--- {path} ---")
    if not path.exists():
        print("FILE NOT FOUND")
        continue
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        features = data.get("features", [])
        if data.get("type") == "Feature":
            features = [data]
        types = {}
        coords = []
        for feature in features:
            geom = feature.get("geometry") or {}
            typ = geom.get("type", "None")
            types[typ] = types.get(typ, 0) + 1
            coords.extend(walk_coords(geom.get("coordinates", [])))
        print("Feature count:", len(features))
        print("Geometry types:", types)
        print("CRS metadata:", data.get("crs", "not specified"))
        if coords:
            xs = [p[0] for p in coords]
            ys = [p[1] for p in coords]
            print("Coordinate bounds:", min(xs), min(ys), max(xs), max(ys))
        if features:
            print("First feature property names:",
                  list((features[0].get("properties") or {}).keys())[:15])
    except Exception as e:
        print("Could not read:", e)
