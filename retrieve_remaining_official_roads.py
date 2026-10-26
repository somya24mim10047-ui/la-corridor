
from pathlib import Path
import requests
import geopandas as gpd
from shapely.geometry import shape

BASE = Path(__file__).resolve().parent
OUT = BASE / "data" / "boundary_candidates"
OUT.mkdir(parents=True, exist_ok=True)

URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

# Search envelopes around the existing business datasets.
CORRIDORS = {
    "vermont_avenue": {
        "name": "VERMONT",
        "suffix": "AVE",
        "business_file": BASE / "data" / "corridors"
        / "vermont_avenue_businesses.csv",
        "bounds": (-118.310, 34.000, -118.280, 34.130),
    },
    "larchmont_boulevard": {
        "name": "LARCHMONT",
        "suffix": "BLVD",
        "business_file": BASE / "data" / "corridors"
        / "larchmont_boulevard_businesses.csv",
        "bounds": (-118.330, 34.060, -118.300, 34.100),
    },
}

def query(params):
    response = requests.get(URL, params=params, timeout=90)
    response.raise_for_status()
    result = response.json()

    if "error" in result:
        raise RuntimeError(result["error"])

    return result

for corridor, cfg in CORRIDORS.items():
    print(f"\n=== {corridor.upper()} ===")

    if not cfg["business_file"].exists():
        print(f"Business file missing: {cfg['business_file']}")
        continue

    minx, miny, maxx, maxy = cfg["bounds"]

    params = {
        "where": (
            f"STNAME='{cfg['name']}' "
            f"AND STSFX='{cfg['suffix']}'"
        ),
        "geometry": f"{minx},{miny},{maxx},{maxy}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT",
        "returnGeometry": "false",
        "returnIdsOnly": "true",
        "f": "json",
    }

    result = query(params)
    ids = result.get("objectIds") or []

    if not ids:
        print("No matching official road IDs found. Check name/suffix.")
        continue

    print(f"Official matching IDs: {len(ids)}")

    features = []

    # Fetch in batches to avoid service response limits.
    for start in range(0, len(ids), 100):
        batch = ids[start:start + 100]

        result = query({
            "objectIds": ",".join(map(str, batch)),
            "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT",
            "returnGeometry": "true",
            "outSR": 4326,
            "f": "geojson",
        })

        features.extend(result.get("features", []))

    # Save the complete official retrieval for auditability.
    source_file = OUT / f"{corridor}_official_full_retrieval.geojson"

    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    gdf = gdf[gdf.geometry.notna()].copy()

    if not gdf.empty:
        gdf = gdf[gdf.geometry.is_valid].copy()

    gdf.to_file(source_file, driver="GeoJSON")

    print(f"Saved official features: {len(gdf)}")
    print(f"Saved: {source_file}")

    # Report coverage for a manual sanity check.
    roads_metric = gdf.to_crs("EPSG:32611")
    total_km = roads_metric.geometry.length.sum() / 1000
    print(f"Total retrieved road length: {total_km:.3f} km")

print("\nOfficial retrieval finished.")
