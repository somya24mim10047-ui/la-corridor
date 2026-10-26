
import json
from pathlib import Path

folder = Path("data/boundary_candidates/complete_road_sources")

for file in sorted(folder.glob("*_complete_clean.geojson")):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    types = sorted({
        feature.get("geometry", {}).get("type", "None")
        for feature in features
    })

    coordinates = []

    def collect_coords(obj):
        if isinstance(obj, (list, tuple)):
            if (
                len(obj) >= 2
                and isinstance(obj[0], (int, float))
                and isinstance(obj[1], (int, float))
            ):
                coordinates.append((obj[0], obj[1]))
            else:
                for item in obj:
                    collect_coords(item)

    for feature in features:
        geometry = feature.get("geometry")
        if geometry:
            collect_coords(geometry.get("coordinates", []))

    print(f"\n{'=' * 50}")
    print("File:", file.name)
    print("Feature count:", len(features))
    print("Geometry types:", types)

    if coordinates:
        longitudes = [point[0] for point in coordinates]
        latitudes = [point[1] for point in coordinates]

        print("Longitude range:", min(longitudes), "to", max(longitudes))
        print("Latitude range:", min(latitudes), "to", max(latitudes))

print("\nGeometry check complete. No files modified.")
