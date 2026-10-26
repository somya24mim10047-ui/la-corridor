
from pathlib import Path
import requests
import pandas as pd

BASE = Path(__file__).resolve().parent
AUDIT = BASE / "data" / "boundary_candidates" / "all_corridor_audit"

URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

EXCEPTIONS = {
    "Wilshire Place": {
        "name": "WILSHIRE PLACE",
        "suffix": "PL",
        "bounds": (-118.300, 34.050, -118.275, 34.070),
    },
    "Olympic Boulevard": {
        "name": "OLYMPIC",
        "suffix": "BLVD",
        "bounds": (-118.350, 34.040, -118.320, 34.065),
    },
    "Vermont Avenue": {
        "name": "VERMONT",
        "suffix": "AVE",
        "bounds": (-118.315, 34.065, -118.290, 34.090),
    },
}

def query(params):
    response = requests.get(URL, params=params, timeout=90)
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise RuntimeError(result["error"])
    return result

for label, cfg in EXCEPTIONS.items():
    print(f"\n=== {label.upper()} ===")
    minx, miny, maxx, maxy = cfg["bounds"]

    result = query({
        "where": (
            f"STNAME='{cfg['name']}' AND STSFX='{cfg['suffix']}'"
        ),
        "geometry": f"{minx},{miny},{maxx},{maxy}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT",
        "returnGeometry": "false",
        "returnIdsOnly": "false",
        "resultRecordCount": 1000,
        "f": "json",
    })

    features = result.get("features", [])
    print(f"Official matching road records: {len(features)}")

    rows = [feature.get("attributes", {}) for feature in features]
    if rows:
        df = pd.DataFrame(rows)
        cols = [
            c for c in ["OBJECTID", "STNAME", "STSFX", "ADRF", "ADRT"]
            if c in df.columns
        ]
        print(df[cols].to_string(index=False))
    else:
        print("No matching street records in this search area.")

print("\nVerification finished. No project files were modified.")
