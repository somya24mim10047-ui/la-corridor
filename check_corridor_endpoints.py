
import json
from pathlib import Path

folder = Path("data/boundary_candidates/complete_road_sources")

for file in sorted(folder.glob("*_complete_clean.geojson")):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    records = []

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry") or {}
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

        collect(geometry.get("coordinates", []))

        if points:
            records.append({
                "id": props.get("OBJECTID"),
                "name": props.get("STNAME"),
                "suffix": props.get("STSFX"),
                "from": props.get("ADRF"),
                "to": props.get("ADRT"),
                "min_lat": min(p[1] for p in points),
                "max_lat": max(p[1] for p in points),
                "min_lon": min(p[0] for p in points),
                "max_lon": max(p[0] for p in points),
            })

    print(f"\n{'=' * 65}\n{file.name}")

    for label, key in [
        ("SOUTHERNMOST", "min_lat"),
        ("NORTHERNMOST", "max_lat"),
        ("WESTERNMOST", "min_lon"),
        ("EASTERNMOST", "max_lon"),
    ]:
        row = min(records, key=lambda r: r[key]) if key.endswith("lat") and label == "SOUTHERNMOST" else (
            max(records, key=lambda r: r[key]) if key.endswith("lat") else (
                min(records, key=lambda r: r[key]) if label == "WESTERNMOST" else
                max(records, key=lambda r: r[key])
            )
        )

        print(
            f"{label}: OBJECTID={row['id']}, "
            f"{row['name']} {row['suffix']}, "
            f"ADRF={row['from']}, ADRT={row['to']}, "
            f"lat={row['min_lat']:.6f}..{row['max_lat']:.6f}, "
            f"lon={row['min_lon']:.6f}..{row['max_lon']:.6f}"
        )

print("\nEndpoint check complete. No files modified.")
