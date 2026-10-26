
import json
from pathlib import Path

files = [
    Path("data/boundary_candidates/olympic_boulevard_official_full_retrieval.geojson"),
    Path("data/boundary_candidates/complete_road_sources/olympic_boulevard_complete_clean.geojson"),
]

all_ids = []

for path in files:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    ids = {
        feature.get("properties", {}).get("OBJECTID")
        for feature in features
    }

    all_ids.append(ids)

    print(f"\nFile: {path.name}")
    print(f"Feature count: {len(features)}")
    print(f"Unique OBJECTIDs: {len(ids)}")

    ranges = sorted(
        (
            feature.get("properties", {}).get("ADRF"),
            feature.get("properties", {}).get("ADRT"),
            feature.get("properties", {}).get("OBJECTID"),
        )
        for feature in features
    )

    print("Address ranges (ADRF, ADRT, OBJECTID):")
    for item in ranges:
        print(item)

print("\nSOURCE COMPARISON")
print("IDs in original but missing from cleaned:", sorted(all_ids[0] - all_ids[1], key=str))
print("IDs in cleaned but missing from original:", sorted(all_ids[1] - all_ids[0], key=str))
print("\nComparison complete. No files modified.")
