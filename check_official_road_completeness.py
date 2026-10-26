
from pathlib import Path
import requests
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent
ROAD_DIR = ROOT / "data" / "corridors"
OUT_DIR = ROOT / "data" / "boundary_candidates"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

corridors = {
    "wilshire_boulevard": {
        "name": "WILSHIRE",
        "bounds": (-118.350, 34.050, -118.275, 34.075),
    },
    "olympic_boulevard": {
        "name": "OLYMPIC",
        "bounds": (-118.350, 34.035, -118.275, 34.060),
    },
}

for corridor, info in corridors.items():
    xmin, ymin, xmax, ymax = info["bounds"]

    params = {
        "where": (
            f"STNAME = '{info['name']}' "
            "AND STSFX = 'BLVD'"
        ),
        "geometry": f"{xmin},{ymin},{xmax},{ymax}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT",
        "returnGeometry": "true",
        "outSR": 4326,
        "returnIdsOnly": "true",
        "f": "json",
    }

    response = requests.get(URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        print(corridor, "API ERROR:", data["error"])
        continue

    ids = data.get("objectIds") or []
    print(f"\n{corridor.upper()}: official matching IDs found: {len(ids)}")

    if not ids:
        continue

    # Retrieve records in batches to avoid response-size limits.
    records = []
    for start in range(0, len(ids), 100):
        batch_params = {
            "objectIds": ",".join(map(str, ids[start:start + 100])),
            "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT",
            "returnGeometry": "true",
            "outSR": 4326,
            "f": "geojson",
        }
        r = requests.get(URL, params=batch_params, timeout=60)
        r.raise_for_status()
        payload = r.json()

        if "features" in payload:
            records.extend(payload["features"])

    if not records:
        print("No features returned in detail requests.")
        continue

    full_path = OUT_DIR / f"{corridor}_official_full_retrieval.geojson"
    import json
    full_path.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": records,
        }),
        encoding="utf-8",
    )

    full = gpd.read_file(full_path)
    existing_path = ROAD_DIR / f"{corridor}_road_segments_clean.geojson"
    existing = gpd.read_file(existing_path)

    full_ids = set(full["OBJECTID"].astype(int))
    existing_ids = set(existing["OBJECTID"].astype(int))
    missing_ids = sorted(full_ids - existing_ids)

    print("Full retrieval features:", len(full))
    print("Existing cleaned features:", len(existing))
    print("New feature IDs:", len(missing_ids))

    if missing_ids:
        missing = full[full["OBJECTID"].astype(int).isin(missing_ids)]
        print(
            missing[["OBJECTID", "STNAME", "STSFX", "ADRF", "ADRT"]]
            .to_string(index=False)
        )
        missing.to_file(
            OUT_DIR / f"{corridor}_additional_official_segments.geojson",
            driver="GeoJSON",
        )

print("\nOfficial road completeness check complete.")
